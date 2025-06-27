
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

OCCUPATION_DATA_PATH = '../data/OccupationData.xlsx'
SKILLS_DATA_PATH = '../data/Skills.xlsx'
ABILITIES_DATA_PATH = '../data/Abilities.xlsx'
DATABASE_URL = os.getenv('DATABASE_URL')

ROW_LIMIT = 2200 

# --- 1. Data Extraction --- #
def extract_data(occupation_path, skills_path, row_limit=None):
    print(f"Extracting data from {occupation_path} and {skills_path}...")
    try:
        df_occupation = pd.read_excel(occupation_path, nrows=row_limit)
        df_skills = pd.read_excel(skills_path, nrows=row_limit)
        print("Data extracted successfully.")
        return df_occupation, df_skills
    except FileNotFoundError as e:
        print(f"Error: One or more Excel files not found. Please check paths.\n{e}")
        exit()
    except Exception as e:
        print(f"An error occurred during data extraction: {e}")
        exit()

# --- 2. Data Cleaning and Transformation --- #
def transform_data(df_occupation, df_skills):
    print("Cleaning and transforming data...")
    # Clean occupation data
    df_occupation.columns = df_occupation.columns.str.strip().str.replace(" ", "_").str.replace("", "", regex=False).str.lower()
    print(f"Occupation DataFrame columns after initial cleaning: {df_occupation.columns.tolist()}")
    # Check for the correct column name after initial cleaning
    if 'o*net-soc_code' in df_occupation.columns:
        df_occupation = df_occupation.rename(columns={'o*net-soc_code': 'onet_soc_code'})
    elif 'o_net-soc_code' in df_occupation.columns:
        df_occupation = df_occupation.rename(columns={'o_net-soc_code': 'onet_soc_code'})
    print(f"Occupation DataFrame columns after renaming: {df_occupation.columns.tolist()}")
    df_occupation = df_occupation.drop_duplicates(subset=['onet_soc_code'])
    df_occupation['description'] = df_occupation['description'].fillna('')

    # Clean skills data
    df_skills.columns = df_skills.columns.str.strip().str.replace(" ", "_").str.replace("", "", regex=False).str.lower()
    print(f"Skills DataFrame columns after initial cleaning: {df_skills.columns.tolist()}")
    # Check for the correct column name after initial cleaning
    if 'o*net-soc_code' in df_skills.columns:
        df_skills = df_skills.rename(columns={'o*net-soc_code': 'onet_soc_code'})
    elif 'onet-soc_code' in df_skills.columns:
        df_skills = df_skills.rename(columns={'onet-soc_code': 'onet_soc_code'})
    elif 'o_net-soc_code' in df_skills.columns:
        df_skills = df_skills.rename(columns={'o_net-soc_code': 'onet_soc_code'})
    
    print(f"Skills DataFrame columns after renaming: {df_skills.columns.tolist()}")
    df_skills = df_skills.drop_duplicates()
    # Fill NaN in 'not_relevant' with 'N' for consistency if it indicates relevance
    df_skills['not_relevant'] = df_skills['not_relevant'].fillna('N')
    # Convert 'data_value' to numeric, coercing errors
    df_skills['data_value'] = pd.to_numeric(df_skills['data_value'], errors='coerce')
    df_skills = df_skills.dropna(subset=['data_value']) # Drop rows where data_value couldn't be converted

    # Join dataframes
    # Assuming 'onet_soc_code' is the common key
    df_combined = pd.merge(df_occupation, df_skills, on='onet_soc_code', how='left')
    if 'title_x' in df_combined.columns and 'title_y' in df_combined.columns:
        df_combined = df_combined.drop(columns=['title_y'])
        df_combined = df_combined.rename(columns={'title_x': 'title'})
    df_combined['date'] = pd.to_datetime(df_combined['date'], format='%m/%Y', errors='coerce')
    print("Data cleaned and transformed successfully.")
    return df_combined

# --- 3. Data Loading to PostgreSQL --- #
def load_data_to_db(df, db_url):
    print("Loading data to PostgreSQL database...")
    try:
        engine = create_engine(db_url)
        with engine.connect() as connection:
            # Create tables if they don't exist
            # For simplicity, we'll create one combined table. In a real app, you'd normalize.
            connection.execute(text("""
CREATE TABLE IF NOT EXISTS job_competencies (
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
"""))
            connection.execute(text("TRUNCATE TABLE job_competencies;")) # Clear existing data for fresh load
            connection.commit()
            # Load data into the table
            df.to_sql('job_competencies', engine, if_exists='append', index=False)
            print("Data loaded to job_competencies table successfully.")
    except Exception as e:
        print(f"An error occurred during database loading: {e}")
        exit()

# --- Main Execution --- #
if __name__ == "__main__":
    df_occ, df_sk = extract_data(OCCUPATION_DATA_PATH, SKILLS_DATA_PATH, ROW_LIMIT)
    df_combined = transform_data(df_occ, df_sk)
    load_data_to_db(df_combined, DATABASE_URL)
    print("Data ingestion process completed.")


