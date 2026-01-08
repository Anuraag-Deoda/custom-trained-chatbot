import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import re

# --- Configuration ---
# Load environment variables from a .env file if it exists
load_dotenv()

# Define file paths for all O*NET data sources.
BASE_DATA_PATH = os.getenv('DATA_PATH', '../data') 
OCCUPATION_DATA_PATH = os.path.join(BASE_DATA_PATH, 'OccupationData.xlsx')
SKILLS_DATA_PATH = os.path.join(BASE_DATA_PATH, 'Skills.xlsx')
ABILITIES_DATA_PATH = os.path.join(BASE_DATA_PATH, 'Abilities.xlsx')
KNOWLEDGE_DATA_PATH = os.path.join(BASE_DATA_PATH, 'Knowledge.xlsx')
TASKS_DATA_PATH = os.path.join(BASE_DATA_PATH, 'Tasks.xlsx')

DATABASE_URL = os.getenv('DATABASE_URL')
ROW_LIMIT = None # Set to None to process all rows

# --- 1. Intelligent Data Extraction and Cleaning ---

def clean_column_names(df):
    """
    Standardizes all column names in a DataFrame to a consistent format.
    """
    cleaned_columns = {}
    for col in df.columns:
        new_col = col.strip().lower()
        new_col = re.sub(r'[^a-z0-9]+', '_', new_col)
        
        if 'o_net_soc_code' in new_col:
            cleaned_columns[col] = 'onet_soc_code'
        else:
            cleaned_columns[col] = new_col
            
    df = df.rename(columns=cleaned_columns)
    return df

def process_source_file(file_path, file_type, row_limit=None):
    """
    Reads an Excel file, cleans it, and prepares it for transformation.
    """
    print(f"Processing {file_type} from {file_path}...")
    try:
        df = pd.read_excel(file_path, nrows=row_limit)
    except FileNotFoundError:
        print(f"ERROR: File not found at {file_path}. Please check the path.")
        return None
    except Exception as e:
        print(f"ERROR: Could not read Excel file {file_path}. Reason: {e}")
        return None

    df = clean_column_names(df)
    
    if 'onet_soc_code' not in df.columns:
        print(f"ERROR: 'onet_soc_code' column could not be identified in {file_type}. Skipping file.")
        return None

    if file_type in ['Skills', 'Abilities', 'Knowledge']:
        df['element_type'] = file_type.rstrip('s')
        numeric_cols = ['data_value', 'n', 'standard_error', 'lower_ci_bound', 'upper_ci_bound']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        if 'not_relevant' in df.columns:
            df['not_relevant'] = df['not_relevant'].fillna('N')
        if 'recommend_suppress' in df.columns:
            df['recommend_suppress'] = df['recommend_suppress'].fillna('N')
        
        df.dropna(subset=['data_value'], inplace=True)

    elif file_type == 'Tasks':
        df['element_type'] = 'Task'
        df = df.rename(columns={'task_id': 'element_id', 'task': 'element_name'})
        
        if 'task_type' in df.columns:
            df['task_type'] = df['task_type'].fillna('Not Specified')
        
        if 'data_value' not in df.columns:
            df['data_value'] = 1.0
        if 'scale_name' not in df.columns:
            df['scale_name'] = 'Task Relevance'
            
        df.dropna(subset=['element_name'], inplace=True)

    elif file_type == 'Occupations':
        if 'description' in df.columns:
            df['description'] = df['description'].fillna('No description available.')
        df = df.drop_duplicates(subset=['onet_soc_code'])

    if 'date' in df.columns:
        # FIX: Specify date format to resolve UserWarning and ensure correct parsing.
        df['date'] = pd.to_datetime(df['date'], format='%m/%Y', errors='coerce')
        
    print(f"Successfully cleaned {len(df)} rows for {file_type}.")
    return df

# --- 2. Data Transformation and Combination ---

def transform_and_combine(dataframes):
    """
    Combines all processed dataframes into a single, unified structure.
    """
    print("Combining all data sources...")
    
    occupations_df = dataframes.get('Occupations')
    if occupations_df is None:
        print("ERROR: Occupation data is missing. Cannot proceed with merging.")
        return None

    element_dfs = [df for key, df in dataframes.items() if key != 'Occupations' and df is not None]
    
    if not element_dfs:
        print("ERROR: No competency or task data found to process.")
        return None

    combined_elements_df = pd.concat(element_dfs, ignore_index=True, sort=False)
    
    # FIX: Drop the 'title' column from the combined elements before merging.
    # This prevents the 'title_x' and 'title_y' collision that causes the KeyError.
    # The authoritative title will come from the occupations_df.
    if 'title' in combined_elements_df.columns:
        combined_elements_df = combined_elements_df.drop(columns=['title'])

    # Merge with occupation data to add the job title and description
    occupation_meta_cols = ['onet_soc_code', 'title', 'description']
    final_df = pd.merge(
        combined_elements_df,
        occupations_df[occupation_meta_cols],
        on='onet_soc_code',
        how='left'
    )
    
    # This dropna call will now work correctly as 'title' will exist.
    final_df.dropna(subset=['title'], inplace=True)
    
    print(f"Successfully combined all data into a single DataFrame with {len(final_df)} rows.")
    return final_df

# --- 3. Data Loading ---

def load_to_postgres(df, db_url):
    """
    Loads the final, combined DataFrame into a PostgreSQL database.
    """
    if df is None or df.empty:
        print("No data to load. Aborting database operation.")
        return
        
    if not db_url:
        print("ERROR: DATABASE_URL environment variable is not set. Cannot connect.")
        return

    print("Connecting to PostgreSQL and loading data...")
    try:
        engine = create_engine(db_url)
        table_name = 'job_competencies'
        
        # Use pandas to_sql for efficient bulk loading and schema creation.
        df.to_sql(
            table_name,
            engine,
            if_exists='replace',
            index=False,
            chunksize=1000
        )
        
        with engine.connect() as connection:
            connection.execute(text(f'ALTER TABLE {table_name} ADD COLUMN id SERIAL PRIMARY KEY;'))
            connection.commit()

        print(f"Successfully loaded {len(df)} records into '{table_name}' table.")

    except Exception as e:
        print(f"An error occurred during database loading: {e}")

# --- Main Execution Block ---

if __name__ == "__main__":
    print("--- Starting O*NET Data Ingestion Pipeline ---")

    sources = {
        'Occupations': OCCUPATION_DATA_PATH,
        'Skills': SKILLS_DATA_PATH,
        'Abilities': ABILITIES_DATA_PATH,
        'Knowledge': KNOWLEDGE_DATA_PATH,
        'Tasks': TASKS_DATA_PATH
    }

    processed_dataframes = {name: process_source_file(path, name, ROW_LIMIT) for name, path in sources.items()}
    final_dataframe = transform_and_combine(processed_dataframes)
    load_to_postgres(final_dataframe, DATABASE_URL)

    print("--- Data Ingestion Pipeline Completed ---")