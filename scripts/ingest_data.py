import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

OCCUPATION_DATA_PATH = '../data/OccupationData.xlsx'
SKILLS_DATA_PATH = '../data/Skills.xlsx'
ABILITIES_DATA_PATH = '../data/Abilities.xlsx' # New: Path for Abilities data
DATABASE_URL = os.getenv('DATABASE_URL')

ROW_LIMIT = 2200 # Limit for processing rows, adjust as needed for your 80k+ line file

# --- 1. Data Extraction --- #
def extract_data(occupation_path, skills_path, abilities_path, row_limit=None):
    """
    Extracts data from Occupation, Skills, and Abilities Excel files.
    """
    print(f"Extracting data from {occupation_path}, {skills_path}, and {abilities_path}...")
    try:
        df_occupation = pd.read_excel(occupation_path, nrows=row_limit)
        df_skills = pd.read_excel(skills_path, nrows=row_limit)
        df_abilities = pd.read_excel(abilities_path, nrows=row_limit)
        print("Data extracted successfully.")
        return df_occupation, df_skills, df_abilities
    except FileNotFoundError as e:
        print(f"Error: One or more Excel files not found. Please check paths.\n{e}")
        exit()
    except Exception as e:
        print(f"An error occurred during data extraction: {e}")
        exit()

# --- 2. Data Cleaning and Transformation --- #
def clean_and_standardize_element_df(df, type_name):
    """
    Cleans and standardizes column names and values in the skills or abilities DataFrame.
    """
    print(f"Cleaning and standardizing {type_name} data...")

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("*", "", regex=False)
        .str.lower()
    )

    print(f"{type_name} DataFrame columns before renaming: {df.columns.tolist()}")

    # Rename all known variants of onet_soc_code
    df = df.rename(columns={
        'onet-soc-code': 'onet_soc_code',
        'onet-soc_code': 'onet_soc_code',
        'o_net-soc-code': 'onet_soc_code',
        'o_net-soc_code': 'onet_soc_code',
        'o_net_soc_code': 'onet_soc_code'
    })

    if 'onet_soc_code' not in df.columns:
        raise KeyError(f"'onet_soc_code' column not found in {type_name} DataFrame after renaming.")

    # Fill NaN values in not_relevant if it exists
    if 'not_relevant' in df.columns:
        df['not_relevant'] = df['not_relevant'].fillna('N')

    # Convert 'data_value' to numeric
    if 'data_value' in df.columns:
        df['data_value'] = pd.to_numeric(df['data_value'], errors='coerce')
        df = df.dropna(subset=['data_value'])

    # Convert 'date' column to datetime if present
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], format='%m/%Y', errors='coerce')

    print(f"{type_name} DataFrame columns after cleaning: {df.columns.tolist()}")
    return df
def transform_data(df_occupation, df_skills, df_abilities):
    """
    Cleans, transforms, and combines occupation, skills, and abilities data.
    """
    print("Cleaning and transforming data...")

    # 1. Clean and standardize occupation data
    df_occupation.columns = (
        df_occupation.columns
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("*", "", regex=False)
        .str.lower()
    )
    print("Occupation DataFrame columns before renaming:", df_occupation.columns.tolist())

    # Rename onet_soc_code variations
    df_occupation = df_occupation.rename(columns={
        'onet-soc-code': 'onet_soc_code',
        'onet-soc_code': 'onet_soc_code',
        'o_net-soc-code': 'onet_soc_code',
        'o_net-soc_code': 'onet_soc_code',
        'o_net_soc_code': 'onet_soc_code'
    })

    if 'onet_soc_code' not in df_occupation.columns:
        raise KeyError("Could not find 'onet_soc_code' in occupation data.")

    df_occupation = df_occupation.drop_duplicates(subset=['onet_soc_code'])
    df_occupation['description'] = df_occupation['description'].fillna('')
    print(f"Occupation DataFrame columns after cleaning: {df_occupation.columns.tolist()}")

    # 2. Clean and standardize skills and abilities
    df_skills_cleaned = clean_and_standardize_element_df(df_skills.copy(), "Skills")
    df_abilities_cleaned = clean_and_standardize_element_df(df_abilities.copy(), "Abilities")

    # Common expected columns
    columns_for_elements = [
        'onet_soc_code', 'element_id', 'element_name', 'scale_id', 'scale_name',
        'data_value', 'n', 'standard_error', 'lower_ci_bound', 'upper_ci_bound',
        'recommend_suppress', 'not_relevant', 'date', 'domain_source'
    ]

    # Filter and label
    df_skills_filtered = df_skills_cleaned[df_skills_cleaned.columns.intersection(columns_for_elements)].copy()
    df_abilities_filtered = df_abilities_cleaned[df_abilities_cleaned.columns.intersection(columns_for_elements)].copy()

    df_skills_filtered['element_type'] = 'Skill'
    df_abilities_filtered['element_type'] = 'Ability'

    # 3. Combine skills and abilities
    df_elements = pd.concat([df_skills_filtered, df_abilities_filtered], ignore_index=True)
    df_elements = df_elements.drop_duplicates()

    # 4. Merge with occupation metadata
    required_cols = ['onet_soc_code', 'title', 'description']
    missing_cols = [col for col in required_cols if col not in df_occupation.columns]
    if missing_cols:
        raise KeyError(f"Missing columns in occupation data for merge: {missing_cols}")

    df_occupation_for_merge = df_occupation[required_cols]
    df_combined = pd.merge(df_elements, df_occupation_for_merge, on='onet_soc_code', how='left')

    print("Data cleaned and transformed successfully.")
    return df_combined
# --- 3. Data Loading to PostgreSQL --- #
def load_data_to_db(df, db_url):
    """
    Loads the combined DataFrame into the PostgreSQL 'job_competencies' table.
    """
    print("Loading data to PostgreSQL database...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            # NEW: Drop the table if it exists to ensure schema updates
            connection.execute(text("DROP TABLE IF EXISTS job_competencies;"))
            connection.commit() # Commit the drop operation

            # Create table with the latest schema (including element_type)
            connection.execute(text("""
CREATE TABLE job_competencies (
    id SERIAL PRIMARY KEY,
    onet_soc_code VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    description TEXT,
    element_id VARCHAR(255),
    element_name VARCHAR(255),
    element_type VARCHAR(50), 
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
"""))
            connection.commit() # Commit the create operation
            
            # Load data into the table
            df.to_sql('job_competencies', engine, if_exists='append', index=False)
            print("Data loaded to job_competencies table successfully.")
    except Exception as e:
        print(f"An error occurred during database loading: {e}")
        exit()

# --- Main Execution --- #
if __name__ == "__main__":
    # Extract data from all three sources
    df_occ, df_sk, df_ab = extract_data(OCCUPATION_DATA_PATH, SKILLS_DATA_PATH, ABILITIES_DATA_PATH, ROW_LIMIT)
    
    # Transform and combine the data
    df_combined = transform_data(df_occ, df_sk, df_ab)
    
    # Load the combined data to the database
    load_data_to_db(df_combined, DATABASE_URL)
    print("Data ingestion process completed.")
