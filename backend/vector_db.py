import os
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any
import json
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CompetencyVectorDB:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.pinecone_api_key = os.getenv('PINECONE_API_KEY')
        self.pinecone_environment = os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp-free')
        self.index_name = 'competency-model'
        self.database_url = os.getenv('DATABASE_URL')
        self.pc = None
        self.index = None
        
    def initialize_pinecone(self):
        """Initialize Pinecone vector database, dropping and recreating if it exists."""
        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            
            # Check if index exists and delete it for a clean start
            existing_indexes = self.pc.list_indexes().names()
            if self.index_name in existing_indexes:
                print(f"Deleting existing Pinecone index: {self.index_name}")
                self.pc.delete_index(self.index_name)
                print(f"Index {self.index_name} deleted.")
            
            # Create index with ServerlessSpec
            print(f"Creating new Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=384,  # all-MiniLM-L6-v2 embedding dimension
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',  # or 'gcp' depending on your preference
                    region='us-east-1'  # adjust region as needed
                )
            )
            
            self.index = self.pc.Index(self.index_name)
            print("Pinecone initialized successfully")
            
        except Exception as e:
            print(f"Error initializing Pinecone: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        return self.model.encode(texts)
    
    def create_job_competency_vectors(self):
        """Create vectors for job competencies from PostgreSQL data"""
        try:
            engine = create_engine(self.database_url)
            
            # Query job competencies data (now includes element_type)
            query = """
            SELECT 
                onet_soc_code,
                title,
                description,
                element_name,
                element_type, 
                scale_name,
                data_value
            FROM job_competencies 
            WHERE data_value IS NOT NULL
            ORDER BY onet_soc_code, data_value DESC
            """
            
            df = pd.read_sql(query, engine)
            
            # Group by job role and create comprehensive descriptions
            job_descriptions = []
            job_metadata = []
            
            for onet_code, group in df.groupby('onet_soc_code'):
                title = group['title'].iloc[0]
                description = group['description'].iloc[0]
                
                # Get top skills and abilities for this role for embedding
                top_skills = group[group['element_type'] == 'Skill'].nlargest(5, 'data_value')
                top_abilities = group[group['element_type'] == 'Ability'].nlargest(5, 'data_value')

                skill_text = "; ".join([
                    f"{row['element_name']} ({row['scale_name']}): {row['data_value']}"
                    for _, row in top_skills.iterrows()
                ])
                ability_text = "; ".join([
                    f"{row['element_name']} ({row['scale_name']}): {row['data_value']}"
                    for _, row in top_abilities.iterrows()
                ])
                
                # Create comprehensive job description
                full_description = (
                    f"Job Title: {title}. Description: {description}. "
                    f"Key Skills: {skill_text}. "
                    f"Key Abilities: {ability_text}"
                )
                
                job_descriptions.append(full_description)
                job_metadata.append({
                    'onet_soc_code': onet_code,
                    'title': title,
                    'description': description,
                    'competency_count': len(group)
                })
            
            # Generate embeddings
            embeddings = self.generate_embeddings(job_descriptions)
            
            # Prepare vectors for Pinecone
            vectors = []
            for i, (embedding, metadata) in enumerate(zip(embeddings, job_metadata)):
                vectors.append({
                    'id': f"job_{metadata['onet_soc_code']}",
                    'values': embedding.tolist(),
                    'metadata': {
                        **metadata,
                        'text': job_descriptions[i]
                    }
                })
            
            # Upsert to Pinecone in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            print(f"Successfully created {len(vectors)} job competency vectors")
            return len(vectors)
            
        except Exception as e:
            print(f"Error creating job competency vectors: {e}")
            raise
    
    def search_similar_jobs(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar jobs based on query"""
        try:
            # Generate embedding for query
            query_embedding = self.generate_embeddings([query])[0]
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True
            )
            
            # Format results
            similar_jobs = []
            for match in results['matches']:
                similar_jobs.append({
                    'job_id': match['id'],
                    'score': match['score'],
                    'title': match['metadata']['title'],
                    'description': match['metadata']['description'],
                    'onet_soc_code': match['metadata']['onet_soc_code'],
                    'competency_count': match['metadata']['competency_count']
                })
            
            return similar_jobs
            
        except Exception as e:
            print(f"Error searching similar jobs: {e}")
            raise
    
    def get_job_competencies(self, onet_soc_code: str) -> Dict[str, Any]:
        """Get detailed competencies for a specific job, structured by type and scale."""
        try:
            engine = create_engine(self.database_url)
            
            query = """
            SELECT 
                element_name,
                element_type, 
                scale_name,
                data_value,
                element_id,
                scale_id
            FROM job_competencies 
            WHERE onet_soc_code = %s
            ORDER BY element_type, scale_name, data_value DESC
            """
            
            df = pd.read_sql(query, engine, params=(onet_soc_code,))
            
            # Group competencies by element_type (Skill/Ability) and then by scale
            structured_competencies = {}
            for _, row in df.iterrows():
                element_type = row['element_type']
                scale = row['scale_name']
                
                if element_type not in structured_competencies:
                    structured_competencies[element_type] = {}
                
                if scale not in structured_competencies[element_type]:
                    structured_competencies[element_type][scale] = []
                
                structured_competencies[element_type][scale].append({
                    'element_name': row['element_name'],
                    'data_value': float(row['data_value']),
                    'element_id': row['element_id'],
                    'scale_id': row['scale_id']
                })
            
            return structured_competencies
            
        except Exception as e:
            print(f"Error getting job competencies: {e}")
            raise

class CompetencyAnalyzer:
    def __init__(self, vector_db: CompetencyVectorDB):
        self.vector_db = vector_db
    
    def analyze_job_role(self, job_title: str) -> Dict[str, Any]:
        """Analyze a job role and provide competency insights"""
        try:
            # Search for similar jobs
            similar_jobs = self.vector_db.search_similar_jobs(job_title, top_k=3)
            
            if not similar_jobs:
                return {"error": "No similar jobs found"}
            
            # Get detailed competencies for the most similar job
            best_match = similar_jobs[0]
            competencies = self.vector_db.get_job_competencies(best_match['onet_soc_code'])
            
            # Create filtered competency framework (top 3 only)
            filtered_competencies = self._filter_top_competencies(competencies)
            
            # Create competency framework
            framework = {
                'job_analysis': {
                    'query': job_title,
                    'best_match': best_match,
                    'similar_jobs': similar_jobs
                },
                'competency_framework': filtered_competencies,  # Now filtered to top 3
                'recommendations': self._generate_recommendations(filtered_competencies),
                'formatted_framework_summary': self._format_competency_framework_summary(filtered_competencies),
                'structural_diagram': self._create_structural_data(filtered_competencies)  # Graph with top 3 only
            }
            
            return framework
            
        except Exception as e:
            print(f"Error analyzing job role: {e}")
            raise
    
    def _filter_top_competencies(self, structured_competencies: Dict[str, Any], top_n: int = 3) -> Dict[str, Any]:
        """Filter competencies to keep only top N by importance"""
        filtered = {}
        
        for element_type, scales in structured_competencies.items():
            filtered[element_type] = {}
            
            for scale_name, competencies in scales.items():
                # Sort by data_value (importance/level) and take top N
                sorted_competencies = sorted(
                    competencies, 
                    key=lambda x: x['data_value'], 
                    reverse=True
                )
                filtered[element_type][scale_name] = sorted_competencies[:top_n]
        
        return filtered
    
    def _generate_recommendations(self, structured_competencies: Dict[str, Any]) -> List[str]:
        """Generate concise recommendations (top 3 skills/abilities by importance) for the initial chat response."""
        recommendations = []

        # Get top 3 Skills by Importance
        if 'Skill' in structured_competencies and 'Importance' in structured_competencies['Skill']:
            top_skills_importance = sorted(
                structured_competencies['Skill']['Importance'],
                key=lambda x: x['data_value'],
                reverse=True
            )[:3]
            for i, skill in enumerate(top_skills_importance):
                recommendations.append(
                    f"Skill {i+1}: {skill['element_name']} (Importance: {skill['data_value']:.1f})"
                )

        # Get top 3 Abilities by Importance
        if 'Ability' in structured_competencies and 'Importance' in structured_competencies['Ability']:
            top_abilities_importance = sorted(
                structured_competencies['Ability']['Importance'],
                key=lambda x: x['data_value'],
                reverse=True
            )[:3]
            for i, ability in enumerate(top_abilities_importance):
                recommendations.append(
                    f"Ability {i+1}: {ability['element_name']} (Importance: {ability['data_value']:.1f})"
                )
        
        # Add a general recommendation if no specific top items found or to provide more context
        if not recommendations:
            recommendations.append("No specific top skills or abilities by importance found for this role.")
        else:
            recommendations.insert(0, "Key competencies for this role (top 3 by Importance):") # Add a header

        return recommendations

    def _format_competency_framework_summary(self, structured_competencies: Dict[str, Any]) -> str:
        """
        Formats a detailed text summary of the competency framework,
        including top 3 skills and abilities by importance and level.
        This is intended for the '📊 Key Competency Framework' section.
        """
        framework_text = '\n📊 Key Competency Framework (Top 3 by Importance & Level):\n\n'

        # Process Skills
        if 'Skill' in structured_competencies:
            framework_text += "--- SKILLS ---\n"
            for scale_name in ['Importance', 'Level']: # Iterate over specific scales
                if scale_name in structured_competencies['Skill']:
                    competencies = structured_competencies['Skill'][scale_name]
                    sorted_competencies = sorted(competencies, key=lambda x: x['data_value'], reverse=True)
                    
                    framework_text += f"  {scale_name.upper()}:\n"
                    for i, comp in enumerate(sorted_competencies[:3]): # Take top 3
                        score = comp['data_value'] if comp['data_value'] is not None else 'N/A';
                        framework_text += f"    {i + 1}. {comp['element_name']} ({score:.1f})\n"
                    framework_text += "\n"
        
        # Process Abilities
        if 'Ability' in structured_competencies:
            framework_text += "--- ABILITIES ---\n"
            for scale_name in ['Importance', 'Level']: # Iterate over specific scales
                if scale_name in structured_competencies['Ability']:
                    competencies = structured_competencies['Ability'][scale_name]
                    sorted_competencies = sorted(competencies, key=lambda x: x['data_value'], reverse=True)
                    
                    framework_text += f"  {scale_name.upper()}:\n"
                    for i, comp in enumerate(sorted_competencies[:3]): # Take top 3
                        score = comp['data_value'] if comp['data_value'] is not None else 'N/A';
                        framework_text += f"    {i + 1}. {comp['element_name']} ({score:.1f})\n"
                    framework_text += "\n"

        return framework_text
    
    def _create_structural_data(self, structured_competencies: Dict[str, Any]) -> Dict[str, Any]:
        """Create structural data for diagram generation, now with filtered competencies only."""
        structure = {
            'nodes': [],
            'edges': [],
            'categories': [] # Will be populated dynamically
        }
        
        node_id_counter = 0
        
        # Add root node for the job
        job_node_id = f"node_{node_id_counter}"
        structure['nodes'].append({
            'id': job_node_id,
            'label': 'Job Role',
            'type': 'job_root',
            'level': 0,
            'group': 'job_root'
        })
        node_id_counter += 1

        # Add element type nodes (Skills, Abilities)
        for element_type, scales in structured_competencies.items():
            type_node_id = f"node_{node_id_counter}"
            structure['nodes'].append({
                'id': type_node_id,
                'label': element_type,
                'type': 'element_type',
                'level': 1,
                'group': 'element_type'
            })
            structure['edges'].append({
                'from': job_node_id,
                'to': type_node_id,
                'weight': 1 # Arbitrary weight
            })
            node_id_counter += 1

            # Add scale nodes (Importance, Level)
            for scale_name, competencies in scales.items():
                scale_node_id = f"node_{node_id_counter}"
                structure['nodes'].append({
                    'id': scale_node_id,
                    'label': scale_name.replace('_', ' '),
                    'type': 'scale',
                    'level': 2,
                    'group': 'scale'
                })
                structure['edges'].append({
                    'from': type_node_id,
                    'to': scale_node_id,
                    'weight': 1 # Arbitrary weight
                })
                node_id_counter += 1

                # Add competency nodes (now filtered to top 3 only)
                for comp in competencies: # This is now already filtered to top 3
                    comp_node_id = f"node_{node_id_counter}"
                    structure['nodes'].append({
                        'id': comp_node_id,
                        'label': f"{comp['element_name']} ({comp['data_value']:.1f})",
                        'type': 'competency',
                        'level': 3,
                        'importance': comp['data_value'],
                        'element_id': comp['element_id'],
                        'scale_id': comp['scale_id'],
                        'element_type': element_type,
                        'scale_name': scale_name,
                        'group': 'competency'
                    })
                    structure['edges'].append({
                        'from': scale_node_id,
                        'to': comp_node_id,
                        'weight': comp['data_value']
                    })
                    node_id_counter += 1
        
        # Populate categories for potential frontend filtering/display
        structure['categories'] = list(structured_competencies.keys()) # e.g., ['Skill', 'Ability']
        for element_type, scales in structured_competencies.items():
            for scale_name in scales.keys():
                structure['categories'].append(f"{element_type} - {scale_name.replace('_', ' ')}")

        return structure

# Example usage and initialization
if __name__ == "__main__":
    # Initialize vector database
    vector_db = CompetencyVectorDB()
    vector_db.initialize_pinecone()
    
    # Initialize analyzer
    analyzer = CompetencyAnalyzer(vector_db)