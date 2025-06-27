# backend/app.py - Flask API for Competency Model Chatbot

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
from vector_db import CompetencyVectorDB, CompetencyAnalyzer  # Updated import
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize global components
vector_db = None
analyzer = None

def initialize_components():
    """Initialize vector database and analyzer"""
    global vector_db, analyzer
    try:
        vector_db = CompetencyVectorDB()
        vector_db.initialize_pinecone()
        analyzer = CompetencyAnalyzer(vector_db)
        logger.info("Components initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing components: {e}")
        raise

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Competency Model Chatbot API is running"
    })

@app.route("/api/analyze-job", methods=["POST"])
def analyze_job():
    """Analyze a job role and return competency framework"""
    try:
        data = request.get_json()
        
        if not data or "job_title" not in data:
            return jsonify({
                "error": "job_title is required"
            }), 400
        
        job_title = data["job_title"].strip()
        
        if not job_title:
            return jsonify({
                "error": "job_title cannot be empty"
            }), 400
        
        # Analyze the job role
        result = analyzer.analyze_job_role(job_title)
        
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logger.error(f"Error analyzing job: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route("/api/search-jobs", methods=["POST"])
def search_jobs():
    """Search for similar jobs based on query"""
    try:
        data = request.get_json()
        
        if not data or "query" not in data:
            return jsonify({
                "error": "query is required"
            }), 400
        
        query = data["query"].strip()
        top_k = data.get("top_k", 5)
        
        if not query:
            return jsonify({
                "error": "query cannot be empty"
            }), 400
        
        # Search for similar jobs
        similar_jobs = vector_db.search_similar_jobs(query, top_k)
        
        return jsonify({
            "success": True,
            "data": {
                "query": query,
                "similar_jobs": similar_jobs
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route("/api/job-competencies/<onet_soc_code>", methods=["GET"])
def get_job_competencies(onet_soc_code):
    """Get detailed competencies for a specific job"""
    try:
        competencies = vector_db.get_job_competencies(onet_soc_code)
        
        return jsonify({
            "success": True,
            "data": {
                "onet_soc_code": onet_soc_code,
                "competencies": competencies
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting job competencies: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    """Chat endpoint for conversational interface"""
    try:
        data = request.get_json()
        
        if not data or "message" not in data:
            return jsonify({
                "error": "message is required"
            }), 400
        
        message = data["message"].strip()
        
        if not message:
            return jsonify({
                "error": "message cannot be empty"
            }), 400
        
        # Simple chat logic - analyze if it looks like a job title
        if any(keyword in message.lower() for keyword in ["engineer", "manager", "analyst", "developer", "specialist", "coordinator", "director"]):
            # Treat as job analysis request
            result = analyzer.analyze_job_role(message)
            
            response = f"I found information about {message}. Here's the competency analysis:\n\n"
            
            if "job_analysis" in result:
                best_match = result["job_analysis"]["best_match"]
                response += f"Best match: {best_match['title']} (similarity: {best_match['score']:.2f})\n\n"
            
            if "recommendations" in result:
                response += "Key recommendations:\n"
                for i, rec in enumerate(result["recommendations"][:3], 1):
                    response += f"{i}. {rec}\n"
            print(f"Response: {response}") 
            print(f"Result: {result}")
            print(f"Type: job_analysis")

            logger.info(f"first block ======== Chat response: {response}")
            logger.info(f"first block ======== Analysis result: {result}")
            logger.info(f"first block ======== Type: job_analysis")
            return jsonify({
                "success": True,
                "data": {
                    "response": response,
                    "analysis": result,
                    "type": "job_analysis"
                }
            })
        else:
            # General search
            similar_jobs = vector_db.search_similar_jobs(message, 3)
            
            if similar_jobs:
                response = f"I found {len(similar_jobs)} jobs related to {message}:\n\n"
                for i, job in enumerate(similar_jobs, 1):
                    response += f"{i}. {job['title']} (similarity: {job['score']:.2f})\n"
                response += "\nWould you like me to analyze any of these roles in detail?"
            else:
                response = f"I couldn't find any jobs directly related to {message}. Try being more specific or use job titles like 'Software Engineer' or 'Data Analyst'."
            
            print(f"Response: {response}")
            print(f"Similar Jobs: {similar_jobs}")
            print(f"Type: search")
            logger.info(f"Chat response: {response}")
            logger.info(f"Similar jobs: {similar_jobs}")
            logger.info(f"Type: search")
            return jsonify({
                "success": True,
                "data": {
                    "response": response,
                    "similar_jobs": similar_jobs,
                    "type": "search"
                }
            })
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500



@app.route("/api/initialize-vectors", methods=["POST"])
def initialize_vectors():
    """Initialize vector database with job competency data"""
    try:
        count = vector_db.create_job_competency_vectors()
        
        return jsonify({
            "success": True,
            "data": {
                "message": f"Successfully created {count} job competency vectors",
                "count": count
            }
        })
        
    except Exception as e:
        logger.error(f"Error initializing vectors: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found"
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error"
    }), 500

if __name__ == "__main__":
    try:
        # Initialize components
        initialize_components()
        
        # Run the app
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port, debug=True)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise