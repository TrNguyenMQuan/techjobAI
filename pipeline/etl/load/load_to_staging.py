"""
Load Parquet file from Azure Data Lake Gen2 into PostgreSQL staging.raw_jobs table.
Medallion: Silver (Staging) Layer
Usage:
    python pipeline/etl/load/load_to_staging.py
"""

import json
import os
import sys
from datetime import date
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from azure.storage.filedatalake import DataLakeServiceClient

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# ============================================================
# CONFIG
# ============================================================
load_dotenv(PROJECT_ROOT / "infra/.env")

DB_USER = os.getenv("POSTGRES_USER", "techjob")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "techjob123")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "techjob_ai")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER = os.getenv("AZURE_CONTAINER_NAME", "techjob-datalake")

today_str = date.today().isoformat()
REMOTE_PATH = f"raw/vietnamworks/{today_str}/jobs.parquet"
TEMP_CACHE_PATH = PROJECT_ROOT / f"data/cache/vietnamworks/{today_str}/jobs.parquet"


# ============================================================
# AZURE DOWNLOAD HELPER
# ============================================================
def download_from_azure(remote_path: str, local_path: str):
    """Download raw parquet from Azure Data Lake Gen2."""
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)

    if not AZURE_CONNECTION_STRING:
        raise ValueError("[ERROR] AZURE_STORAGE_CONNECTION_STRING not set in env.")

    remote_path_str = str(remote_path).replace("\\", "/")

    service_client = DataLakeServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    filesystem_client = service_client.get_file_system_client(AZURE_CONTAINER)

    parts = remote_path_str.rsplit("/", 1)
    if len(parts) == 2:
        dir_name, file_name = parts
        directory_client = filesystem_client.get_directory_client(dir_name)
    else:
        file_name = parts[0]
        directory_client = filesystem_client

    file_client = directory_client.get_file_client(file_name)
    with open(local_path, "wb") as f:
        download = file_client.download_file()
        f.write(download.readall())


# ============================================================
# DATA CLEANING & SCHEMATIZATION
# ============================================================
def clean_and_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Clean, handle nulls/duplicates, and normalize schemas using Pandas."""
    print(f"[CLEANING] Starting data cleaning on {len(df)} raw rows...")

    # 1. Deduplicate by source_id
    before_count = len(df)
    df = df.drop_duplicates(subset=["source_id"], keep="last")
    print(f"  -> Deduplication: removed {before_count - len(df)} duplicates")

    # 2. Filter out records missing source_id or title
    df = df[df["source_id"].notna() & (df["source_id"].astype(str).str.strip() != "")]
    df = df[df["title"].notna() & (df["title"].astype(str).str.strip() != "")]
    print(f"  -> Filtered missing critical fields: {len(df)} rows remaining")

    # 3. Strip whitespace and fill missing text columns with defaults
    df["title"] = df["title"].astype(str).str.strip()
    df["company_name"] = df["company_name"].fillna("Unknown Company").astype(str).str.strip()
    
    text_cols = ["address", "job_description", "job_requirement", "industry", "language", "source_url"]
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    # 4. Normalize numeric columns
    if "salary_min" in df.columns:
        df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce").fillna(0).astype(int)
    if "salary_max" in df.columns:
        df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce").fillna(0).astype(int)

    # 5. Ensure JSON columns are valid JSON arrays/objects
    json_cols = ["location_cities", "skills", "benefits"]
    for col in json_cols:
        if col in df.columns:
            # If string representation is missing, default to empty array
            df[col] = df[col].fillna("[]").astype(str).str.strip()
            cleaned_vals = []
            for val in df[col]:
                try:
                    parsed = json.loads(val)
                    if not isinstance(parsed, (list, dict)):
                        cleaned_vals.append("[]")
                    else:
                        cleaned_vals.append(val)
                except Exception:
                    cleaned_vals.append("[]")
            df[col] = cleaned_vals

    # 6. Normalize date strings
    date_cols = ["created_on", "approved_on", "expired_on", "online_on"]
    for col in date_cols:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()

    print(f"  -> Data cleaning completed. Returning {len(df)} cleaned rows.")
    return df


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"{'=' * 60}")
    print(f"  Load to Staging — {today_str}")
    print(f"  Source: Azure Data Lake Gen2")
    print(f"{'=' * 60}")

    # 1. Download file from Azure Data Lake
    print(f"\n[INFO] Downloading raw data from Azure: {REMOTE_PATH}...")
    try:
        download_from_azure(REMOTE_PATH, str(TEMP_CACHE_PATH))
        print(f"  [OK] Downloaded successfully to: {TEMP_CACHE_PATH}")
    except Exception as e:
        print(f"[ERROR] Could not download file from Azure: {e}")
        print(f"  -> Ensure extract_vietnamworks & upload_to_azure have run!")
        return

    # 2. Read Parquet
    df = pd.read_parquet(TEMP_CACHE_PATH)
    print(f"[INFO] Read {len(df)} raw rows from downloaded file")

    # 3. Clean and Schematize Data
    df = clean_and_normalize(df)

    # 4. Connect to DB
    engine = create_engine(DATABASE_URL)
    print(f"[INFO] Connected to PostgreSQL: {DB_HOST}:{DB_PORT}/{DB_NAME}")

    # 5. Upsert into staging.raw_jobs
    insert_count = 0

    upsert_sql = text("""
        INSERT INTO staging.raw_jobs (
            source_id, raw_title, raw_company_name, raw_location,
            raw_salary, raw_experience, raw_job_type, raw_work_mode,
            raw_description, raw_requirements, raw_benefits,
            raw_skills, raw_company_size, raw_logo_url,
            raw_source_url, raw_posted_date, raw_deadline,
            raw_payload, ingested_at, is_processed
        ) VALUES (
            :source_id, :raw_title, :raw_company_name, :raw_location,
            :raw_salary, :raw_experience, :raw_job_type, :raw_work_mode,
            :raw_description, :raw_requirements, :raw_benefits,
            :raw_skills, :raw_company_size, :raw_logo_url,
            :raw_source_url, :raw_posted_date, :raw_deadline,
            :raw_payload, NOW(), FALSE
        )
        ON CONFLICT (source_id) DO UPDATE SET
            raw_title = EXCLUDED.raw_title,
            raw_company_name = EXCLUDED.raw_company_name,
            raw_location = EXCLUDED.raw_location,
            raw_salary = EXCLUDED.raw_salary,
            raw_description = EXCLUDED.raw_description,
            raw_requirements = EXCLUDED.raw_requirements,
            raw_benefits = EXCLUDED.raw_benefits,
            raw_skills = EXCLUDED.raw_skills,
            raw_logo_url = EXCLUDED.raw_logo_url,
            raw_source_url = EXCLUDED.raw_source_url,
            raw_posted_date = EXCLUDED.raw_posted_date,
            raw_deadline = EXCLUDED.raw_deadline,
            raw_payload = EXCLUDED.raw_payload,
            ingested_at = NOW(),
            is_processed = FALSE
    """)

    all_params = []
    for _, row in df.iterrows():
        # Build full payload JSON
        payload = {
            "job_id": row.get("job_id"),
            "company_id": row.get("company_id"),
            "salary_min": int(row.get("salary_min", 0)),
            "salary_max": int(row.get("salary_max", 0)),
            "salary_currency": row.get("salary_currency"),
            "is_salary_visible": row.get("is_salary_visible"),
            "job_level": row.get("job_level"),
            "job_level_vi": row.get("job_level_vi"),
            "industry": row.get("industry"),
            "type_working_id": row.get("type_working_id"),
            "language": row.get("language"),
            "created_on": row.get("created_on"),
            "approved_on": row.get("approved_on"),
            "online_on": row.get("online_on"),
            "extracted_at": row.get("extracted_at"),
        }

        # Map salary display to raw_salary
        salary_text = row.get("salary_display", "")
        if row.get("salary_min") and row.get("salary_max") and row["salary_min"] > 0:
            salary_text = f"{row['salary_min']}-{row['salary_max']} {row.get('salary_currency', '')}"
        elif row.get("salary_display"):
            salary_text = row["salary_display"]

        params = {
            "source_id": row["source_id"],
            "raw_title": row["title"],
            "raw_company_name": row["company_name"],
            "raw_location": row.get("location_cities", ""),
            "raw_salary": salary_text,
            "raw_experience": row.get("job_level_vi", ""),
            "raw_job_type": "",
            "raw_work_mode": str(row.get("type_working_id", "")),
            "raw_description": row.get("job_description", ""),
            "raw_requirements": row.get("job_requirement", ""),
            "raw_benefits": row.get("benefits", ""),
            "raw_skills": row.get("skills", ""),
            "raw_company_size": "",
            "raw_logo_url": row.get("company_logo", ""),
            "raw_source_url": row.get("source_url", ""),
            "raw_posted_date": row.get("approved_on", ""),
            "raw_deadline": row.get("expired_on", ""),
            "raw_payload": json.dumps(payload, ensure_ascii=False, default=str),
        }
        all_params.append(params)

    if all_params:
        with engine.begin() as conn:
            conn.execute(upsert_sql, all_params)
        insert_count = len(all_params)

    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  Rows loaded to DB : {insert_count}")
    print(f"  Table             : staging.raw_jobs")
    print(f"{'=' * 60}")

    # 6. Verify count
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM staging.raw_jobs"))
        total = result.scalar()
        print(f"\n[VERIFY] staging.raw_jobs total rows: {total}")

    # 7. Cleanup temp file
    if TEMP_CACHE_PATH.exists():
        try:
            TEMP_CACHE_PATH.unlink()
            print("[CLEANUP] Deleted temp cache Parquet file.")
        except Exception as e:
            print(f"[CLEANUP] [WARNING] Failed to delete temp cache file: {e}")


if __name__ == "__main__":
    main()
