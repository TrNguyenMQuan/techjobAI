from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from pipeline.bronze import run as bronze_run
from pipeline.silver import run as silver_run
from pipeline.silver_to_postgres import run as silver_to_posgre_run
from pipeline.embedding import run as embedding_run

default_args = {
    "owner" : "techjobai",
    "retries" : 2,
    "retry_delay" : timedelta(minutes=5)
}

with DAG(
    dag_id= "vietnamworks_etl",
    default_args= default_args,
    start_date= datetime(2026, 5, 26),
    schedule_interval= "@daily",
    catchup= False,
    tags= ["vietnamworks", "etl"],
) as dag:
    
    ingest_to_bronze = PythonOperator(
        task_id="ingest_to_bronze",
        python_callable=bronze_run,
        op_kwargs={"date_str": "{{ ds }}"},
    )

    extract_to_silver = PythonOperator(
        task_id= "extract_to_silver",
        python_callable= silver_run,
        op_kwargs={"date_str": "{{ ds }}"},
    )

    silver_to_postgres = PythonOperator(
        task_id= "silver_to_postgres",
        python_callable= silver_to_posgre_run,
        op_kwargs={"date_str": "{{ ds }}"},
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_vietnamworks && /home/airflow/.local/bin/dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_vietnamworks && /home/airflow/.local/bin/dbt test --profiles-dir .",
    )

    generate_embeddings = PythonOperator(
        task_id="generate_embeddings",
        python_callable=embedding_run,
    )

    ingest_to_bronze >> extract_to_silver >> silver_to_postgres >> dbt_run >> dbt_test >> generate_embeddings
