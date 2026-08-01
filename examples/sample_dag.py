"""
Sample Airflow DAG for PyAirflowTester testing.

This DAG demonstrates various patterns that PyAirflowTester analyzes.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

# Good practice: Define defaults
default_args = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    dag_id="sample_etl_pipeline",
    default_args=default_args,
    description="Sample ETL pipeline for testing PyAirflowTester",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["sample", "etl"],
    # Good practice: Define SLA
    sla=timedelta(hours=2),
    # Good practice: Set reasonable concurrency
    max_active_runs=1,
)


def extract_data():
    """Extract data from source."""
    print("Extracting data...")
    return {"extracted": True}


def transform_data(**context):
    """Transform extracted data."""
    print("Transforming data...")
    return {"transformed": True}


def load_data():
    """Load data to warehouse."""
    print("Loading data...")


# Task definitions
extract_task = PythonOperator(
    task_id="extract_data",
    python_callable=extract_data,
    dag=dag,
    pool="data_pool",
)

transform_task = PythonOperator(
    task_id="transform_data",
    python_callable=transform_data,
    dag=dag,
    pool="data_pool",
)

load_task = PythonOperator(
    task_id="load_data",
    python_callable=load_data,
    dag=dag,
    pool="data_pool",
)

# Run dbt models
dbt_run_task = BashOperator(
    task_id="dbt_run",
    bash_command="dbt run",
    dag=dag,
)

# Run dbt tests
dbt_test_task = BashOperator(
    task_id="dbt_test",
    bash_command="dbt test",
    dag=dag,
    retries=1,
)

# Notification task
notify_task = DummyOperator(
    task_id="send_notification",
    dag=dag,
    trigger_rule="all_done",
)

# Define task dependencies
extract_task >> transform_task >> load_task
load_task >> dbt_run_task
dbt_run_task >> dbt_test_task
[load_task, dbt_test_task] >> notify_task

if __name__ == "__main__":
    dag.cli()
