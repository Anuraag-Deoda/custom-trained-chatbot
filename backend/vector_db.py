import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import openai
import hashlib
from datetime import datetime, timedelta
from functools import lru_cache
from tqdm import tqdm

# --- Configuration ---
# Load environment variables and set API keys
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

# --- Advanced Caching Layer ---
class CacheManager:
    """
    Manages a versioned, time-to-live (TTL) file-based JSON cache for
    expensive operations like API calls.
    """
    def __init__(self, cache_dir='cache', version='1.0', ttl_days=30):
        self.cache_dir = cache_dir
        self.version = version
        self.ttl = timedelta(days=ttl_days)
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        self.cache_files = {
            'llm_descriptions': os.path.join(self.cache_dir, 'llm_descriptions_cache.json'),
            'llm_analysis': os.path.join(self.cache_dir, 'llm_analysis_cache.json')
        }
        self.caches = {key: self._load_cache(file) for key, file in self.cache_files.items()}
        print(f"CacheManager initialized. Version: {self.version}, TTL: {ttl_days} days. Loaded {sum(len(c) for c in self.caches.values())} items.")

    def _load_cache(self, file_path: str) -> Dict:
        """Loads a JSON cache file from disk."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_cache(self, cache_name: str):
        """Saves a cache dictionary to a JSON file."""
        with open(self.cache_files[cache_name], 'w') as f:
            json.dump(self.caches[cache_name], f, indent=2)

    def get(self, cache_name: str, key: str) -> Any:
        """
        Gets an item from the specified cache if it exists, is the correct
        version, and has not expired.
        """
        cached_item = self.caches[cache_name].get(key)
        if not cached_item:
            return None

        # Check version
        if cached_item.get('version') != self.version:
            return None # Stale version

        # Check TTL
        created_at = datetime.fromisoformat(cached_item.get('created_at', '1970-01-01'))
        if datetime.now() > created_at + self.ttl:
            return None # Expired

        print(f"🧠 Used cached item from '{cache_name}' for key starting with '{key[:10]}...'")
        return cached_item.get('data')

    def set(self, cache_name: str, key: str, value: Any):
        """Sets an item in the specified cache with version and timestamp."""
        payload = {
            'data': value,
            'created_at': datetime.now().isoformat(),
            'version': self.version
        }
        self.caches[cache_name][key] = payload
        self._save_cache(cache_name)

    @staticmethod
    def create_key(data: str) -> str:
        """Creates a consistent SHA256 hash for a string to use as a cache key."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

class CompetencyVectorDB:
    """
    Manages the creation and querying of job competency vectors in Pinecone,
    enhanced with an LLM and an advanced caching layer.
    """
    def __init__(self, cache_manager: CacheManager):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.index_name = 'advanced-competency-model'
        self.pc = None
        self.index = None
        self.cache = cache_manager

    def initialize_pinecone(self):
        """Initialize Pinecone, deleting and recreating the index for a clean start."""
        if not PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY environment variable not set.")
            
        print(f"Initializing Pinecone with index: {self.index_name}...")
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        if self.index_name in self.pc.list_indexes().names():
            print(f"Deleting existing index '{self.index_name}'...")
            self.pc.delete_index(self.index_name)
        
        self.pc.create_index(
            name=self.index_name,
            dimension=self.model.get_sentence_embedding_dimension(),
            metric='cosine',
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        self.index = self.pc.Index(self.index_name)
        print("Pinecone initialized successfully.")

    @lru_cache(maxsize=256) # In-memory cache for the current session
    def _get_llm_enhanced_description(self, title: str, description: str, elements_summary: str) -> str:
        """
        Uses an LLM to generate a rich summary, with file-based caching for persistence.
        """
        cache_key = self.cache.create_key(f"{title}-{description}-{elements_summary}")
        
        cached_description = self.cache.get('llm_descriptions', cache_key)
        if cached_description:
            return cached_description

        prompt = f"""
        Based on O*NET data for '{title}', write a dense paragraph synthesizing the description with its critical competencies. This summary is for a vector embedding, so it must be rich with keywords and context.

        Official Description: {description}
        Key Competencies: {elements_summary}

        Synthesize this into a professional, descriptive paragraph.
        """
        try:
            print(f"🚀 Calling GPT-3.5 to enhance description for '{title}'...")
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=256
            )
            new_description = response.choices[0].message.content.strip()
            self.cache.set('llm_descriptions', cache_key, new_description)
            return new_description
        except Exception as e:
            print(f"Warning: LLM enhancement failed for '{title}'. Falling back. Error: {e}")
            return f"Job Title: {title}. Description: {description}. Competencies: {elements_summary}"

    def create_job_competency_vectors(self):
        """
        Fetches job data, generates embeddings (using cache), and upserts to Pinecone with a progress bar.
        """
        print("Creating job competency vectors...")
        engine = create_engine(DATABASE_URL)
        query = "SELECT onet_soc_code, title, description, element_name, element_type, data_value FROM job_competencies WHERE data_value IS NOT NULL"
        df = pd.read_sql(query, engine)
        
        vectors_to_upsert = []
        
        job_groups = list(df.groupby('onet_soc_code'))
        for onet_code, group in tqdm(job_groups, desc="Generating Embeddings"):
            title = group['title'].iloc[0]
            description = group['description'].iloc[0]
            
            element_types = ['Skill', 'Ability', 'Knowledge', 'Task']
            top_elements_summary = [
                f"Key {e_type}s: " + ", ".join(group[group['element_type'] == e_type].nlargest(5, 'data_value')['element_name'].tolist())
                for e_type in element_types if not group[group['element_type'] == e_type].empty
            ]
            elements_text = ". ".join(top_elements_summary)

            enhanced_description = self._get_llm_enhanced_description(title, description, elements_text)
            embedding = self.model.encode(enhanced_description).tolist()

            vectors_to_upsert.append({
                'id': f"job_{onet_code}",
                'values': embedding,
                'metadata': {'onet_soc_code': onet_code, 'title': title, 'text_for_embedding': enhanced_description}
            })

        print(f"Generated {len(vectors_to_upsert)} vectors. Upserting to Pinecone...")
        batch_size = 100
        for i in tqdm(range(0, len(vectors_to_upsert), batch_size), desc="Upserting to Pinecone"):
            self.index.upsert(vectors=vectors_to_upsert[i:i + batch_size])
            
        print("Successfully created and stored all job competency vectors.")

class CompetencyAnalyzer:
    """
    Analyzes job roles using the vector DB and an LLM, with a caching layer.
    Includes an agentic layer for generating contextual follow-up suggestions.
    """
    def __init__(self, vector_db: CompetencyVectorDB):
        self.vector_db = vector_db
        self.cache = vector_db.cache

    def get_similar_jobs(self, onet_code: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Finds jobs similar to the given job based on vector similarity.
        """
        try:
            engine = create_engine(DATABASE_URL)
            # Get the job's embedding text
            query = text("SELECT title FROM job_competencies WHERE onet_soc_code = :code LIMIT 1")
            result = pd.read_sql(query, engine, params={'code': onet_code})
            if result.empty:
                return []

            job_title = result.iloc[0]['title']
            query_embedding = self.vector_db.model.encode(job_title).tolist()

            # Query Pinecone for similar jobs (get more to filter out self)
            results = self.vector_db.index.query(
                vector=query_embedding,
                top_k=limit + 1,
                include_metadata=True
            )

            similar_jobs = []
            for match in results['matches']:
                if match['metadata']['onet_soc_code'] != onet_code:
                    similar_jobs.append({
                        'onet_soc_code': match['metadata']['onet_soc_code'],
                        'title': match['metadata']['title'],
                        'similarity_score': round(match['score'] * 100, 1)
                    })
                if len(similar_jobs) >= limit:
                    break

            return similar_jobs
        except Exception as e:
            print(f"Error getting similar jobs: {e}")
            return []

    def generate_follow_up_suggestions(self, query: str, matched_job: Dict, similar_jobs: List[Dict]) -> List[Dict[str, str]]:
        """
        Generates contextual follow-up suggestions based on the analysis results.
        Returns a list of suggestion objects with 'text' and 'action' keys.
        """
        suggestions = []
        job_title = matched_job.get('title', '')
        onet_code = matched_job.get('onet_soc_code', '')

        # Always suggest exploring similar roles
        if similar_jobs:
            top_similar = similar_jobs[0]['title']
            suggestions.append({
                'text': f"Compare with {top_similar}",
                'action': f"Compare {job_title} with {top_similar}",
                'type': 'compare'
            })

        # Suggest skill deep-dive
        suggestions.append({
            'text': f"What are the key skills for {job_title}?",
            'action': f"What are the key skills for {job_title}?",
            'type': 'skills'
        })

        # Suggest career path
        suggestions.append({
            'text': f"Show career progression from {job_title}",
            'action': f"What career paths lead from {job_title}?",
            'type': 'career'
        })

        # Suggest salary/demand info (placeholder for future)
        suggestions.append({
            'text': "Show similar job roles",
            'action': f"What jobs are similar to {job_title}?",
            'type': 'similar'
        })

        # Suggest gap analysis
        suggestions.append({
            'text': "Analyze my skill gaps for this role",
            'action': f"skill_gap_analysis:{onet_code}",
            'type': 'gap_analysis'
        })

        return suggestions[:4]  # Return top 4 suggestions

    def analyze_job_role(self, job_title_query: str, top_k: int = 3) -> Dict[str, Any]:
        """Provides a comprehensive analysis of a job role, with caching for the final analysis."""
        print(f"\nAnalyzing job role for query: '{job_title_query}'")
        try:
            query_embedding = self.vector_db.model.encode(job_title_query).tolist()
            results = self.vector_db.index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
            
            if not results['matches']:
                return {"error": "No similar job roles found in the database."}

            best_match = results['matches'][0]['metadata']
            best_match_code = best_match['onet_soc_code']
            
            engine = create_engine(DATABASE_URL)
            query = text("SELECT element_type, element_name, data_value FROM job_competencies WHERE onet_soc_code = :code ORDER BY element_type, data_value DESC")
            df_competencies = pd.read_sql(query, engine, params={'code': best_match_code})

            competency_summary = self._create_competency_summary(df_competencies)
            llm_analysis = self._get_llm_analysis(job_title_query, best_match['title'], competency_summary)

            # FIX: Generate structural data for the graph visualization
            structural_diagram = self._create_structural_data(df_competencies, best_match['title'])

            # Agentic layer: Get similar jobs and generate follow-up suggestions
            similar_jobs = self.get_similar_jobs(best_match_code, limit=5)
            matched_job_info = {
                'title': best_match['title'],
                'onet_soc_code': best_match_code
            }
            follow_up_suggestions = self.generate_follow_up_suggestions(
                job_title_query, matched_job_info, similar_jobs
            )

            return {
                "query": job_title_query,
                "best_match_found": best_match['title'],
                "match_details": [r['metadata'] for r in results['matches']],
                "llm_generated_analysis": llm_analysis,
                "structural_diagram": structural_diagram,
                "similar_jobs": similar_jobs,
                "follow_up_suggestions": follow_up_suggestions
            }
        except Exception as e:
            print(f"An error occurred during job role analysis: {e}", exc_info=True)
            return {"error": "An internal error occurred during analysis."}

    def _create_competency_summary(self, df: pd.DataFrame) -> str:
        """Creates a formatted string summary of competencies for an LLM prompt."""
        summary_parts = [
            f"- Top {e_type}s: {', '.join(df[df['element_type'] == e_type].nlargest(7, 'data_value')['element_name'].tolist())}"
            for e_type in df['element_type'].unique() if not df[df['element_type'] == e_type].empty
        ]
        return "\n".join(summary_parts)

    def _create_structural_data(self, df: pd.DataFrame, job_title: str) -> Dict[str, Any]:
        """Creates structural data for the vis.js graph visualization."""
        nodes = []
        edges = []
        node_id_counter = 0

        # Add root node for the job title
        root_id = node_id_counter
        nodes.append({'id': root_id, 'label': job_title, 'group': 'job_root', 'level': 0})
        node_id_counter += 1

        # Create nodes for each competency type
        for e_type in df['element_type'].unique():
            type_id = node_id_counter
            nodes.append({'id': type_id, 'label': e_type, 'group': 'element_type', 'level': 1})
            edges.append({'from': root_id, 'to': type_id})
            node_id_counter += 1

            # Get top 5 competencies for the graph for this type
            df_type = df[df['element_type'] == e_type].nlargest(5, 'data_value')
            
            for _, row in df_type.iterrows():
                comp_id = node_id_counter
                # Shorten long competency names for better graph display
                label = row['element_name']
                if len(label) > 25:
                    label = label[:22] + '...'
                
                nodes.append({
                    'id': comp_id, 
                    'label': f"{label}\n({row['data_value']:.1f})", 
                    'group': 'competency', 
                    'level': 2,
                    'title': f"{row['element_name']}\nImportance/Level: {row['data_value']:.2f}" # Full name in tooltip
                })
                edges.append({'from': type_id, 'to': comp_id, 'value': row['data_value']})
                node_id_counter += 1
                
        return {'nodes': nodes, 'edges': edges}

    @lru_cache(maxsize=32) # In-memory cache for the current session
    def _get_llm_analysis(self, query: str, matched_title: str, competency_summary: str) -> str:
        """Generates a detailed analysis using an LLM, with persistent caching."""
        cache_key = self.cache.create_key(f"{query}-{matched_title}-{competency_summary}")
        
        cached_analysis = self.cache.get('llm_analysis', cache_key)
        if cached_analysis:
            return cached_analysis

        prompt = f"""
        As an expert HR analyst, provide a competency analysis for a user interested in '{query}'.
        The closest O*NET match is '{matched_title}'. 

        Key competencies for this role:
        {competency_summary}

        Provide a structured analysis:
        1.  **Role Essence:** A brief, insightful summary of the role.
        2.  **Core Competency Deep Dive:** Explain the most critical skill, ability, knowledge area, and task.
        3.  **Key Development Path:** Offer 3-4 actionable recommendations for someone aspiring to this role.
        """
        try:
            print(f"🚀 Calling GPT-4o to generate final analysis for '{query}'...")
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            new_analysis = response.choices[0].message.content
            self.cache.set('llm_analysis', cache_key, new_analysis)
            return new_analysis
        except Exception as e:
            print(f"Warning: LLM analysis generation failed. Error: {e}")
            return "Could not generate a detailed analysis due to an API error."

# --- Main Execution Block ---
if __name__ == "__main__":
    print("--- Starting Competency Vectorization and Analysis with Caching ---")
    # 1. Initialize the cache manager
    cache = CacheManager(version='1.1', ttl_days=30)
    # 2. Initialize the vector database
    vector_db = CompetencyVectorDB(cache_manager=cache)
    # Ensure Pinecone is initialized
    vector_db.initialize_pinecone()
    # 3. Create and store vectors
    vector_db.create_job_competency_vectors()
    # 4. Initialize the analyzer
    analyzer = CompetencyAnalyzer(vector_db=vector_db)
    # 5. Perform an analysis on a sample job query
    job_query = "Lead Data Scientist"
    analysis_result = analyzer.analyze_job_role(job_query)
    print("\n--- First Analysis Result ---")
    print(json.dumps(analysis_result, indent=2))
    
    # 6. Perform the same analysis again to demonstrate caching
    analysis_result_cached = analyzer.analyze_job_role(job_query)
    print("\n--- Second (Cached) Analysis Result ---")
    print(json.dumps(analysis_result_cached, indent=2))
    print("\n--- Process Completed ---")
