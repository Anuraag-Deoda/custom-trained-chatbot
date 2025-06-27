# Competency Model Chatbot - Setup and Deployment Guide

## Overview

This is a fully functional competency model chatbot that analyzes job roles and provides detailed competency frameworks. The system uses a PostgreSQL database for structured data, Pinecone for vector search, and provides both a REST API and web interface.

## System Architecture

- **Backend**: Flask API with CORS support
- **Database**: PostgreSQL for structured job/competency data
- **Vector Database**: Pinecone for semantic search
- **ML Model**: Sentence Transformers for text embeddings
- **Frontend**: HTML/CSS/JavaScript web interface
- **Data Processing**: Python scripts for ETL pipeline

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- Pinecone account (free tier available)
- 4GB+ RAM recommended
- Internet connection for initial setup

## Installation Steps

### 1. Extract and Navigate

```bash
# Extract the zip file
unzip competency-model-chatbot.zip
cd competency-model-chatbot
```

### 2. Python Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. PostgreSQL Setup

#### Option A: Local PostgreSQL Installation

1. Install PostgreSQL from https://www.postgresql.org/download/
2. Create database and user:

```sql
-- Connect to PostgreSQL as superuser
CREATE USER manus_user WITH PASSWORD 'manus_password';
CREATE DATABASE competency_db OWNER manus_user;
GRANT ALL PRIVILEGES ON DATABASE competency_db TO manus_user;
```

#### Option B: Docker PostgreSQL (Alternative)

```bash
# Run PostgreSQL in Docker
docker run --name competency-postgres \
  -e POSTGRES_DB=competency_db \
  -e POSTGRES_USER=anuraag \
  -e POSTGRES_PASSWORD=Mitr2024 \
  -p 5432:5432 \
  -d postgres:13
```

### 4. Pinecone Setup

1. Sign up for free account at https://www.pinecone.io/
2. Create a new project
3. Get your API key from the dashboard
4. Note your environment (usually `us-west1-gcp-free` for free tier)

### 5. Environment Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your credentials
# Update PINECONE_API_KEY with your actual API key
# Verify DATABASE_URL matches your PostgreSQL setup
```

### 6. Data Ingestion

```bash
# Place your Excel files in the project directory:
# - OccupationData.xlsx
# - Skills.xlsx

# Run data ingestion (this will process only first 1000 rows for testing)
python ingest_data.py
```

### 7. Vector Database Initialization

```bash
# Start the Flask application
python app.py

# In another terminal, initialize vectors (one-time setup)
curl -X POST http://localhost:5000/api/initialize-vectors
```

## Running the Application

### Start Backend Server

```bash
# Activate virtual environment if not already active
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start Flask server
python app.py
```

The API will be available at `http://localhost:5000`

### Access Web Interface

1. Open `index.html` in your web browser, or
2. Serve it using a simple HTTP server:

```bash
# Python 3
python -m http.server 8000

# Then open http://localhost:8000
```

## API Endpoints

### Health Check
```
GET /health
```

### Analyze Job Role
```
POST /api/analyze-job
Content-Type: application/json

{
  "job_title": "Software Engineer"
}
```

### Search Similar Jobs
```
POST /api/search-jobs
Content-Type: application/json

{
  "query": "data analysis",
  "top_k": 5
}
```

### Get Job Competencies
```
GET /api/job-competencies/{onet_soc_code}
```

### Chat Interface
```
POST /api/chat
Content-Type: application/json

{
  "message": "Tell me about project manager roles"
}
```

## Usage Examples

### Web Interface
1. Open the web interface
2. Type job titles like "Software Engineer", "Data Analyst", "Project Manager"
3. View competency analysis and recommendations
4. Explore similar job roles

### API Usage
```python
import requests

# Analyze a job role
response = requests.post('http://localhost:5000/api/analyze-job', 
                        json={'job_title': 'Software Engineer'})
data = response.json()

# Search for similar jobs
response = requests.post('http://localhost:5000/api/search-jobs',
                        json={'query': 'machine learning', 'top_k': 3})
results = response.json()
```

## Configuration Options

### Database Configuration
- Modify `DATABASE_URL` in `.env` for different database setups
- Adjust `ROW_LIMIT` in `ingest_data.py` for processing more/fewer rows

### Pinecone Configuration
- Change `PINECONE_ENVIRONMENT` if using different region
- Modify `index_name` in `vector_db.py` for custom index names

### Model Configuration
- Change embedding model in `vector_db.py` (line 15)
- Adjust vector dimensions accordingly in Pinecone index creation

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Ensure database and user exist

2. **Pinecone API Error**
   - Verify API key is correct
   - Check environment name
   - Ensure you're within free tier limits

3. **Import Errors**
   - Activate virtual environment
   - Reinstall requirements: `pip install -r requirements.txt`

4. **CORS Errors in Browser**
   - Ensure Flask app is running with CORS enabled
   - Check API_BASE_URL in index.html

5. **No Data Found**
   - Run data ingestion script first
   - Initialize vector database
   - Check Excel file paths

### Performance Optimization

1. **For Large Datasets**
   - Increase `ROW_LIMIT` in `ingest_data.py`
   - Consider batch processing for vector creation
   - Use database indexing for faster queries

2. **Memory Usage**
   - Monitor RAM usage during vector creation
   - Process data in smaller batches if needed
   - Consider using lighter embedding models

## Deployment Options

### Local Development
- Use the setup above for local development and testing

### Production Deployment

#### Option 1: Traditional Server
1. Use production WSGI server (gunicorn):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. Set up reverse proxy (nginx)
3. Use production PostgreSQL instance
4. Configure environment variables for production

#### Option 2: Docker Deployment
```dockerfile
# Dockerfile example
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

#### Option 3: Cloud Deployment
- Deploy to Heroku, AWS, Google Cloud, or Azure
- Use managed PostgreSQL service
- Configure environment variables in cloud platform

## Data Schema

### Job Competencies Table
```sql
CREATE TABLE job_competencies (
    id SERIAL PRIMARY KEY,
    onet_soc_code VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    element_id VARCHAR(255),
    element_name VARCHAR(255),
    scale_id VARCHAR(255),
    scale_name VARCHAR(255),
    data_value NUMERIC,
    n INTEGER,
    standard_error NUMERIC,
    lower_ci_bound NUMERIC,
    upper_ci_bound NUMERIC,
    recommend_suppress VARCHAR(10),
    not_relevant VARCHAR(10),
    date DATE,
    domain_source VARCHAR(255)
);
```

## Security Considerations

1. **Environment Variables**
   - Never commit .env file to version control
   - Use strong database passwords
   - Rotate API keys regularly

2. **Database Security**
   - Use connection pooling in production
   - Implement proper user permissions
   - Enable SSL for database connections

3. **API Security**
   - Add rate limiting for production
   - Implement authentication if needed
   - Validate all input parameters

## Support and Maintenance

### Regular Maintenance
1. Update dependencies regularly
2. Monitor database performance
3. Check Pinecone usage limits
4. Backup database regularly

### Extending the System
1. Add new data sources by modifying `ingest_data.py`
2. Implement new analysis features in `vector_db.py`
3. Enhance UI by modifying `index.html`
4. Add new API endpoints in `app.py`

## License and Credits

This system uses the following open-source libraries:
- Flask for web framework
- Sentence Transformers for embeddings
- Pandas for data processing
- PostgreSQL for database
- Pinecone for vector search

## Contact and Support

For technical issues or questions:
1. Check the troubleshooting section above
2. Review API documentation
3. Check component logs for error details

---

**Note**: This system is designed for development and testing. For production use, implement additional security measures, monitoring, and scaling considerations.

# custom-trained-chatbot
# custom-trained-chatbot
# custom-trained-chatbot
# custom-trained-chatbot
# custom-trained-chatbot
# custom-trained-chatbot
# custom-trained-chatbot
