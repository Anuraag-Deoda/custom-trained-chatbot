from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging
from sqlalchemy import create_engine, text
import pandas as pd
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


# --- New API Endpoints for Advanced Frontend ---

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get dashboard statistics."""
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))

        # Get counts for different element types
        query = text("""
            SELECT
                COUNT(DISTINCT onet_soc_code) as total_jobs,
                COUNT(DISTINCT CASE WHEN element_type = 'Skill' THEN element_name END) as total_skills,
                COUNT(DISTINCT CASE WHEN element_type = 'Ability' THEN element_name END) as total_abilities,
                COUNT(DISTINCT CASE WHEN element_type = 'Knowledge' THEN element_name END) as total_knowledge,
                COUNT(DISTINCT CASE WHEN element_type = 'Task' THEN element_name END) as total_tasks
            FROM job_competencies
        """)
        result = pd.read_sql(query, engine).iloc[0]

        return jsonify({
            "success": True,
            "data": {
                "total_jobs": int(result['total_jobs']),
                "total_skills": int(result['total_skills']),
                "total_abilities": int(result['total_abilities']),
                "total_knowledge": int(result['total_knowledge']),
                "total_tasks": int(result['total_tasks'])
            }
        })
    except Exception as e:
        logger.error(f"Error in /api/stats: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch statistics."}), 500


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    """Get paginated list of all jobs with optional search."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search = request.args.get('search', '', type=str)
        offset = (page - 1) * limit

        engine = create_engine(os.getenv('DATABASE_URL'))

        # Get unique jobs with their descriptions
        if search:
            query = text("""
                SELECT DISTINCT onet_soc_code, title, description
                FROM job_competencies
                WHERE LOWER(title) LIKE LOWER(:search)
                ORDER BY title
                LIMIT :limit OFFSET :offset
            """)
            count_query = text("""
                SELECT COUNT(DISTINCT onet_soc_code) as total
                FROM job_competencies
                WHERE LOWER(title) LIKE LOWER(:search)
            """)
            params = {'search': f'%{search}%', 'limit': limit, 'offset': offset}
        else:
            query = text("""
                SELECT DISTINCT onet_soc_code, title, description
                FROM job_competencies
                ORDER BY title
                LIMIT :limit OFFSET :offset
            """)
            count_query = text("""
                SELECT COUNT(DISTINCT onet_soc_code) as total
                FROM job_competencies
            """)
            params = {'limit': limit, 'offset': offset}

        df = pd.read_sql(query, engine, params=params)
        total = pd.read_sql(count_query, engine, params=params if search else None).iloc[0]['total']

        jobs = df.to_dict('records')

        return jsonify({
            "success": True,
            "data": {
                "jobs": jobs,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": int(total),
                    "pages": (int(total) + limit - 1) // limit
                }
            }
        })
    except Exception as e:
        logger.error(f"Error in /api/jobs: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch jobs."}), 500


@app.route("/api/jobs/<onet_code>", methods=["GET"])
def get_job_detail(onet_code):
    """Get detailed information for a single job including all competencies."""
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))

        # Get job info and all competencies
        query = text("""
            SELECT onet_soc_code, title, description, element_type, element_name, data_value, scale_name
            FROM job_competencies
            WHERE onet_soc_code = :code
            ORDER BY element_type, data_value DESC
        """)
        df = pd.read_sql(query, engine, params={'code': onet_code})

        if df.empty:
            return jsonify({"error": "Job not found."}), 404

        # Structure the response
        job_info = {
            "onet_soc_code": df.iloc[0]['onet_soc_code'],
            "title": df.iloc[0]['title'],
            "description": df.iloc[0]['description']
        }

        # Group competencies by type
        competencies = {}
        for element_type in df['element_type'].unique():
            type_df = df[df['element_type'] == element_type]
            competencies[element_type] = type_df[['element_name', 'data_value', 'scale_name']].to_dict('records')

        return jsonify({
            "success": True,
            "data": {
                "job": job_info,
                "competencies": competencies
            }
        })
    except Exception as e:
        logger.error(f"Error in /api/jobs/{onet_code}: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch job details."}), 500


@app.route("/api/skills", methods=["GET"])
def get_skills():
    """Get list of all unique skills/abilities/knowledge with optional type filter."""
    try:
        element_type = request.args.get('type', None)  # Skill, Ability, Knowledge, Task
        search = request.args.get('search', '', type=str)

        engine = create_engine(os.getenv('DATABASE_URL'))

        # Build query based on filters
        query_parts = ["SELECT DISTINCT element_name, element_type FROM job_competencies WHERE 1=1"]
        params = {}

        if element_type:
            query_parts.append("AND element_type = :element_type")
            params['element_type'] = element_type

        if search:
            query_parts.append("AND LOWER(element_name) LIKE LOWER(:search)")
            params['search'] = f'%{search}%'

        query_parts.append("ORDER BY element_type, element_name")

        query = text(" ".join(query_parts))
        df = pd.read_sql(query, engine, params=params)

        # Group by type
        skills_by_type = {}
        for et in df['element_type'].unique():
            skills_by_type[et] = df[df['element_type'] == et]['element_name'].tolist()

        return jsonify({
            "success": True,
            "data": {
                "skills_by_type": skills_by_type,
                "all_skills": df.to_dict('records')
            }
        })
    except Exception as e:
        logger.error(f"Error in /api/skills: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch skills."}), 500


@app.route("/api/skills/<path:skill_name>/jobs", methods=["GET"])
def get_jobs_by_skill(skill_name):
    """Get all jobs that require a specific skill, sorted by importance."""
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))

        query = text("""
            SELECT DISTINCT jc.onet_soc_code, jc.title, jc.description,
                   jc.element_name, jc.element_type, jc.data_value
            FROM job_competencies jc
            WHERE LOWER(jc.element_name) = LOWER(:skill_name)
            ORDER BY jc.data_value DESC
        """)
        df = pd.read_sql(query, engine, params={'skill_name': skill_name})

        if df.empty:
            return jsonify({
                "success": True,
                "data": {
                    "skill": skill_name,
                    "jobs": []
                }
            })

        jobs = df[['onet_soc_code', 'title', 'description', 'data_value', 'element_type']].to_dict('records')

        return jsonify({
            "success": True,
            "data": {
                "skill": skill_name,
                "element_type": df.iloc[0]['element_type'],
                "jobs": jobs
            }
        })
    except Exception as e:
        logger.error(f"Error in /api/skills/{skill_name}/jobs: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch jobs for skill."}), 500


@app.route("/api/compare", methods=["POST"])
def compare_jobs():
    """Compare multiple jobs side by side."""
    try:
        data = request.get_json()
        job_codes = data.get('job_codes', [])

        if not job_codes or len(job_codes) < 2:
            return jsonify({"error": "At least 2 job codes are required."}), 400

        if len(job_codes) > 4:
            return jsonify({"error": "Maximum 4 jobs can be compared."}), 400

        engine = create_engine(os.getenv('DATABASE_URL'))

        jobs_data = []
        all_competencies = set()

        for code in job_codes:
            query = text("""
                SELECT onet_soc_code, title, description, element_type, element_name, data_value
                FROM job_competencies
                WHERE onet_soc_code = :code
                ORDER BY element_type, data_value DESC
            """)
            df = pd.read_sql(query, engine, params={'code': code})

            if df.empty:
                continue

            job_info = {
                "onet_soc_code": df.iloc[0]['onet_soc_code'],
                "title": df.iloc[0]['title'],
                "description": df.iloc[0]['description'],
                "competencies": {}
            }

            for element_type in df['element_type'].unique():
                type_df = df[df['element_type'] == element_type].nlargest(10, 'data_value')
                job_info['competencies'][element_type] = type_df[['element_name', 'data_value']].to_dict('records')
                all_competencies.update(type_df['element_name'].tolist())

            jobs_data.append(job_info)

        # Find common and unique competencies
        if len(jobs_data) >= 2:
            comp_sets = []
            for job in jobs_data:
                job_comps = set()
                for comps in job['competencies'].values():
                    job_comps.update([c['element_name'] for c in comps])
                comp_sets.append(job_comps)

            common = comp_sets[0].intersection(*comp_sets[1:])
            unique_per_job = [s - common for s in comp_sets]
        else:
            common = set()
            unique_per_job = []

        return jsonify({
            "success": True,
            "data": {
                "jobs": jobs_data,
                "common_competencies": list(common),
                "unique_competencies": [list(u) for u in unique_per_job]
            }
        })
    except Exception as e:
        logger.error(f"Error in /api/compare: {e}", exc_info=True)
        return jsonify({"error": "Failed to compare jobs."}), 500


@app.route("/api/search", methods=["GET"])
def search_autocomplete():
    """Autocomplete search for jobs and skills."""
    try:
        query_str = request.args.get('q', '', type=str)
        search_type = request.args.get('type', 'all')  # 'jobs', 'skills', 'all'
        limit = request.args.get('limit', 10, type=int)

        if not query_str or len(query_str) < 2:
            return jsonify({"success": True, "data": {"jobs": [], "skills": []}})

        engine = create_engine(os.getenv('DATABASE_URL'))
        results = {"jobs": [], "skills": []}

        if search_type in ['jobs', 'all']:
            job_query = text("""
                SELECT DISTINCT onet_soc_code, title
                FROM job_competencies
                WHERE LOWER(title) LIKE LOWER(:search)
                ORDER BY title
                LIMIT :limit
            """)
            job_df = pd.read_sql(job_query, engine, params={'search': f'%{query_str}%', 'limit': limit})
            results['jobs'] = job_df.to_dict('records')

        if search_type in ['skills', 'all']:
            skill_query = text("""
                SELECT DISTINCT element_name, element_type
                FROM job_competencies
                WHERE LOWER(element_name) LIKE LOWER(:search)
                ORDER BY element_name
                LIMIT :limit
            """)
            skill_df = pd.read_sql(skill_query, engine, params={'search': f'%{query_str}%', 'limit': limit})
            results['skills'] = skill_df.to_dict('records')

        return jsonify({"success": True, "data": results})
    except Exception as e:
        logger.error(f"Error in /api/search: {e}", exc_info=True)
        return jsonify({"error": "Search failed."}), 500


@app.route("/api/gap-analysis", methods=["POST"])
def gap_analysis():
    """Analyze skill gaps between user's skills and target job requirements."""
    try:
        data = request.get_json()
        target_job_code = data.get('target_job_code')
        user_skills = data.get('user_skills', [])  # List of {skill_name, proficiency}

        if not target_job_code:
            return jsonify({"error": "Target job code is required."}), 400

        engine = create_engine(os.getenv('DATABASE_URL'))

        # Get target job competencies
        query = text("""
            SELECT element_name, element_type, data_value
            FROM job_competencies
            WHERE onet_soc_code = :code AND element_type IN ('Skill', 'Ability', 'Knowledge')
            ORDER BY data_value DESC
        """)
        df = pd.read_sql(query, engine, params={'code': target_job_code})

        if df.empty:
            return jsonify({"error": "Job not found."}), 404

        # Create a map of user skills
        user_skill_map = {s['skill_name'].lower(): s.get('proficiency', 5) for s in user_skills}

        # Analyze gaps
        gap_analysis_result = []
        matched_skills = []
        missing_skills = []

        for _, row in df.iterrows():
            skill_name = row['element_name']
            required_level = row['data_value']
            user_level = user_skill_map.get(skill_name.lower(), 0)

            gap = required_level - user_level

            item = {
                "skill_name": skill_name,
                "element_type": row['element_type'],
                "required_level": round(required_level, 2),
                "user_level": round(user_level, 2),
                "gap": round(gap, 2),
                "status": "met" if gap <= 0 else ("partial" if user_level > 0 else "missing")
            }
            gap_analysis_result.append(item)

            if user_level > 0:
                matched_skills.append(item)
            else:
                missing_skills.append(item)

        # Calculate overall readiness score
        total_required = sum(r['required_level'] for r in gap_analysis_result)
        total_user = sum(min(r['user_level'], r['required_level']) for r in gap_analysis_result)
        readiness_score = (total_user / total_required * 100) if total_required > 0 else 0

        return jsonify({
            "success": True,
            "data": {
                "target_job_code": target_job_code,
                "readiness_score": round(readiness_score, 1),
                "total_competencies": len(gap_analysis_result),
                "matched_count": len(matched_skills),
                "missing_count": len(missing_skills),
                "gap_details": gap_analysis_result,
                "top_gaps": sorted([g for g in gap_analysis_result if g['gap'] > 0],
                                   key=lambda x: x['gap'], reverse=True)[:10]
            }
        })
    except Exception as e:
        logger.error(f"Error in /api/gap-analysis: {e}", exc_info=True)
        return jsonify({"error": "Gap analysis failed."}), 500


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
