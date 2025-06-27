# vector_db.py - Vector Database and ML Model Components

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
        """Initialize Pinecone vector database"""
        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=self.pinecone_api_key)
            
            # Check if index exists
            existing_indexes = self.pc.list_indexes().names()
            
            if self.index_name not in existing_indexes:
                # Create index with ServerlessSpec
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
            
            # Query job competencies data
            query = """
            SELECT 
                onet_soc_code,
                title,
                description,
                element_name,
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
                
                # Get top competencies for this role
                top_competencies = group.nlargest(10, 'data_value')
                competency_text = "; ".join([
                    f"{row['element_name']} ({row['scale_name']}): {row['data_value']}"
                    for _, row in top_competencies.iterrows()
                ])
                
                # Create comprehensive job description
                full_description = f"Job Title: {title}. Description: {description}. Key Competencies: {competency_text}"
                
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
        """Get detailed competencies for a specific job"""
        try:
            engine = create_engine(self.database_url)
            
            query = """
            SELECT 
                element_name,
                scale_name,
                data_value,
                element_id,
                scale_id
            FROM job_competencies 
            WHERE onet_soc_code = %s
            ORDER BY data_value DESC
            """
            
            # Use positional params (tuple)
            df = pd.read_sql(query, engine, params=(onet_soc_code,))
            
            # Group competencies by scale
            competencies_by_scale = {}
            for _, row in df.iterrows():
                scale = row['scale_name']
                if scale not in competencies_by_scale:
                    competencies_by_scale[scale] = []
                
                competencies_by_scale[scale].append({
                    'element_name': row['element_name'],
                    'data_value': float(row['data_value']),
                    'element_id': row['element_id'],
                    'scale_id': row['scale_id']
                })
            
            return competencies_by_scale
            
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
            
            # Create competency framework
            framework = {
                'job_analysis': {
                    'query': job_title,
                    'best_match': best_match,
                    'similar_jobs': similar_jobs
                },
                'competency_framework': competencies,
                'recommendations': self._generate_recommendations(competencies),
                'structural_diagram': self._create_structural_data(competencies)
            }
            
            return framework
            
        except Exception as e:
            print(f"Error analyzing job role: {e}")
            raise
    
    def _generate_recommendations(self, competencies: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on competencies"""
        recommendations = []
        
        for scale, items in competencies.items():
            if items:
                top_competency = items[0]
                recommendations.append(
                    f"Focus on developing {top_competency['element_name']} "
                    f"in the {scale} area (importance: {top_competency['data_value']:.1f})"
                )
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _create_structural_data(self, competencies: Dict[str, Any]) -> Dict[str, Any]:
        """Create structural data for diagram generation"""
        structure = {
            'nodes': [],
            'edges': [],
            'categories': list(competencies.keys())
        }
        
        # Add category nodes
        for i, category in enumerate(competencies.keys()):
            structure['nodes'].append({
                'id': f"cat_{i}",
                'label': category,
                'type': 'category',
                'level': 0
            })
            
            # Add competency nodes for this category
            for j, competency in enumerate(competencies[category][:5]):  # Top 5 per category
                comp_id = f"comp_{i}_{j}"
                structure['nodes'].append({
                    'id': comp_id,
                    'label': competency['element_name'],
                    'type': 'competency',
                    'level': 1,
                    'importance': competency['data_value']
                })
                
                # Add edge from category to competency
                structure['edges'].append({
                    'from': f"cat_{i}",
                    'to': comp_id,
                    'weight': competency['data_value']
                })
        
        return structure

# Example usage and initialization
if __name__ == "__main__":
    # Initialize vector database
    vector_db = CompetencyVectorDB()
    vector_db.initialize_pinecone()
    
    
    # Initialize analyzer
    analyzer = CompetencyAnalyzer(vector_db)
