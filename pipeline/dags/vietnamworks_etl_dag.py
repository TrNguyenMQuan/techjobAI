"""
Airflow DAG: Daily VietnamWorks ETL Pipeline (Bronze → Silver → Gold → ML/Embedding)
Schedule: Daily at 2:00 AM
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# ============================================================
# CONFIG
# ============================================================
PROJECT_DIR = "/opt/airflow/project"
ETL_DIR = f"{PROJECT_DIR}/pipeline/etl"
DBT_DIR = f"{PROJECT_DIR}/pipeline/dbt"
ML_DIR = f"{PROJECT_DIR}/pipeline/ml"

PYTHON = "python"

default_args = {
    "owner": "data-engineer",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# ============================================================
# DAG DEFINITION
# ============================================================
with DAG(
    dag_id="vietnamworks_etl_dag",
    default_args=default_args,
    description="Orchestrate daily extraction, Azure load, cleaning, staging, warehouse, and job embedding.",
    schedule_interval="0 2 * * *",
    start_date=datetime(2026, 5, 17),
    catchup=False,
    tags=["medallion", "etl", "vietnamworks", "dbt", "embedding"],
) as dag:

    # Task 1: Extract jobs from VietnamWorks API and upload to Azure Data Lake Gen2
    extract = BashOperator(
        task_id="extract_vietnamworks",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} {ETL_DIR}/extract/extract_vietnamworks.py",
    )

    upload_azure = BashOperator(
        task_id="upload_to_azure",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} {ETL_DIR}/load/upload_to_azure.py",
    )

    # Task 2: Load Parquet from Azure Data Lake Gen2, clean and load to Postgres (Silver layer)
    load_to_staging = BashOperator(
        task_id="load_to_staging",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} {ETL_DIR}/load/load_to_staging.py",
    )

    # Task 3: Run dbt models to transform staging data to fact/dimension tables (Gold layer)
    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && dbt run --profiles-dir {DBT_DIR}",
    )

    # Task 4: Execute dbt test cases to verify data quality rules
    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test --profiles-dir {DBT_DIR}",
    )

    # Task 5: Generate Sentence-Transformer embeddings for semantic search in pgvector
    run_embedding = BashOperator(
        task_id="run_embedding",
        bash_command=f"cd {PROJECT_DIR} && {PYTHON} {ML_DIR}/embedding/embedding_service.py",
    )

    # DAG Dependency Flow
    extract >> upload_azure >> load_to_staging >> dbt_run >> dbt_test >> run_embedding
