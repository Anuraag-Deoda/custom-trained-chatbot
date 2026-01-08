from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging
from vector_db import CacheManager, CompetencyVectorDB, CompetencyAnalyzer



# Load environment variables from a .env file
load_dotenv()

# --- App Initialization ---
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes, essential for local development

# Configure logging for better traceability
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global Components ---
# These will be initialized once on startup
cache = None
vector_db = None
analyzer = None

def initialize_components():
    """
    Initializes all backend components in the correct order.
    This function is called once when the Flask app starts.
    """
    global cache, vector_db, analyzer
    try:
        logger.info("Initializing application components...")
        
        # 1. Initialize the Cache Manager
        cache = CacheManager(version='1.1', ttl_days=30)
        
        # 2. Initialize the Vector DB, passing the cache manager to it
        vector_db = CompetencyVectorDB(cache_manager=cache)
        # Note: In a production environment, you might not want to delete and
        # recreate the index on every startup. This is suitable for development.
        vector_db.initialize_pinecone()
        
        # 3. Initialize the Analyzer with the vector_db instance
        analyzer = CompetencyAnalyzer(vector_db=vector_db)
        
        logger.info("✅ All components initialized successfully.")
        
    except Exception as e:
        logger.error(f"❌ Critical error during component initialization: {e}", exc_info=True)
        # In a real app, you might want to exit if components fail to initialize
        raise

# --- API Endpoints ---

@app.route("/")
def homepage():
    return render_template("index.html")

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint to confirm the API is running."""
    return jsonify({"status": "healthy"})

@app.route("/api/chat", methods=["POST"])
def chat():
    """
    Main endpoint for the chat interface. It takes a user message, analyzes it
    as a job query, and returns a structured response for the frontend.
    """
    try:
        data = request.get_json()
        if not data or "message" not in data or not data["message"].strip():
            return jsonify({"error": "A non-empty 'message' is required."}), 400
            
        message = data["message"].strip()
        logger.info(f"Received chat message for analysis: '{message}'")

        # The analyzer is now robust enough to handle any query.
        # It will find the best match and generate a detailed analysis.
        analysis_result = analyzer.analyze_job_role(message)
        
        if "error" in analysis_result:
             return jsonify({
                "success": True, # Return success=true so frontend can display the message
                "data": {
                    "response": analysis_result["error"],
                    "analysis": {},
                    "type": "error"
                }
            })

        # Structure the response to match the frontend's expectations
        response_data = {
            "response": analysis_result.get("llm_generated_analysis", "No analysis available."),
            "analysis": {
                "structural_diagram": analysis_result.get("structural_diagram", {"nodes": [], "edges": []})
            },
            "type": "job_analysis"
        }

        print(f"Analysis result==============================:\n\n {response_data}\n\n\n =========================")

        return jsonify({"success": True, "data": response_data})

    except Exception as e:
        logger.error(f"Error in /api/chat endpoint: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route("/api/rebuild-vectors", methods=["POST"])
def rebuild_vectors():
    """
    An administrative endpoint to manually trigger the creation and upserting
    of all job competency vectors. This is useful after a data update.
    """
    try:
        logger.info("Starting manual vector rebuild process...")
        vector_db.create_job_competency_vectors()
        message = "Successfully rebuilt and stored all job competency vectors in Pinecone."
        logger.info(message)
        return jsonify({"success": True, "message": message})
        
    except Exception as e:
        logger.error(f"Error during manual vector rebuild: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred during vector rebuild."}), 500

# --- Error Handlers ---
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found."}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Caught unhandled internal server error: {error}", exc_info=True)
    return jsonify({"error": "An unexpected internal server error occurred."}), 500

# --- Main Execution Block ---
if __name__ == "__main__":
    try:
        # Initialize components before starting the app
        initialize_components()
        
        # Run the Flask app
        port = int(os.environ.get("PORT", 5000))
        # debug=False is recommended for anything resembling production
        app.run(host="0.0.0.0", port=port, debug=False)
        
    except Exception as e:
        logger.critical(f"❌ Failed to start the Flask application: {e}", exc_info=True)
