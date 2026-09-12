"""Placeholder DAG for Phase 2 (Document Intelligence Pipeline).

This DAG does not parse documents yet — it only proves that Airflow can
see the synthetic corpus generated in Phase 1 (mounted read-only from
backend/datasets). Real parsing tasks (PDF/XLSX extraction via Apache
Tika, cleaning, metadata extraction into PostgreSQL) will replace the
single task here in the next iteration, following the same
Strategy/Factory approach used in Feature 0001.
"""
from datetime import datetime
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

DATASETS_ROOT = Path("/opt/airflow/data/datasets/generated")


def list_generated_documents() -> None:
    if not DATASETS_ROOT.exists():
        print(f"No datasets found yet at {DATASETS_ROOT}.")
        return

    for document_type_dir in sorted(DATASETS_ROOT.iterdir()):
        if document_type_dir.is_dir():
            file_count = len(list(document_type_dir.glob("*")))
            print(f"{document_type_dir.name}: {file_count} file(s)")


with DAG(
    dag_id="list_generated_documents",
    description=(
        "Placeholder for the Document Intelligence Pipeline (Phase 2). "
        "Confirms Airflow can access the Phase 1 synthetic document corpus."
    ),
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    tags=["phase-2", "ingestion-pipeline", "placeholder"],
) as dag:
    list_documents_task = PythonOperator(
        task_id="list_generated_documents",
        python_callable=list_generated_documents,
    )
