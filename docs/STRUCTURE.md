# Project Structure for Competency Model Chatbot

This document outlines a more organized and scalable project structure for the Competency Model Chatbot. This structure separates concerns, making the project easier to navigate, maintain, and extend.

```
competency-model-chatbot/
├── backend/                  # Flask API and core logic
│   ├── app.py                # Main Flask application
│   ├── vector_db.py          # Pinecone integration, embedding generation, and competency analysis logic
│   └── requirements.txt      # Python dependencies for the backend
├── frontend/                 # Web interface (HTML, CSS, JS)
│   └── index.html            # Main chatbot UI
├── data/                     # Raw data files (Excel)
│   ├── OccupationData.xlsx
│   └── Skills.xlsx
├── scripts/                  # Data ingestion and utility scripts
│   └── ingest_data.py        # Script to load data into PostgreSQL and initialize Pinecone
├── docs/                     # Project documentation
│   ├── README.md             # Main project README and quick start guide
│   ├── design_document.md    # Detailed system design and architecture
│   └── STRUCTURE.md          # This document: project directory structure
├── .env.template             # Template for environment variables
└── .gitignore                # Git ignore file (optional, for version control)
```

## Explanation of Directories and Files:

-   **`competency-model-chatbot/`**: The root directory of the project.

-   **`backend/`**:
    -   **`app.py`**: Contains the Flask application, defining API endpoints for chat, job analysis, and data initialization. It acts as the entry point for the backend server.
    -   **`vector_db.py`**: Encapsulates the logic for interacting with Pinecone (vector database), generating embeddings using `SentenceTransformer`, and performing competency analysis. This module handles the core AI/ML aspects.
    -   **`requirements.txt`**: Lists all Python packages required for the backend to run. This ensures consistent environments across development and deployment.

-   **`frontend/`**:
    -   **`index.html`**: The single-page web application that provides the user interface for the chatbot. It includes HTML structure, CSS for styling, and JavaScript for interacting with the backend API.

-   **`data/`**:
    -   **`OccupationData.xlsx`**: The Excel file containing occupation details.
    -   **`Skills.xlsx`**: The Excel file containing skills data.
    
-   **`scripts/`**:
    -   **`ingest_data.py`**: A Python script responsible for the Extract, Transform, Load (ETL) process. It reads data from the Excel files, cleans and transforms it, and then loads it into the PostgreSQL database. It also handles the initial population of the Pinecone vector database.

-   **`docs/`**:
    -   **`README.md`**: The primary documentation file, providing a high-level overview of the project, quick start instructions, and links to more detailed documentation.
    -   **`design_document.md`**: A comprehensive document detailing the system's architecture, design choices, and technical specifications.
    -   **`STRUCTURE.md`**: This document, specifically describing the project's directory layout and the purpose of each component.

-   **`.env.template`**: A template file for environment variables. Users should copy this to `.env` and fill in their sensitive credentials (like API keys and database URLs) before running the application.

-   **`.gitignore`**: (Optional) A file used by Git to specify intentionally untracked files that Git should ignore (e.g., `.env` file, `__pycache__`, `venv/`).

This structure promotes modularity, making it easier to manage dependencies, scale different parts of the application independently, and onboard new developers to the project.

