# Extends the official Airflow image with the Python packages needed
# by ingestion_pipeline's DAG tasks (see backend/ingestion_pipeline/pyproject.toml
# for the source of truth on these dependencies).
FROM apache/airflow:2.9.3

COPY requirements.txt /requirements.txt

# CRITICAL: installing extra packages without Airflow's own constraints
# file lets pip freely upgrade shared dependencies (e.g. SQLAlchemy) to
# versions Airflow's internal ORM models were never tested against,
# breaking the scheduler at import time with cryptic ORM errors. The
# constraints file pins every transitive dependency to versions Airflow
# 2.9.3 on Python 3.12 is actually built and tested with.
RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.9.3/constraints-3.12.txt" \
    -r /requirements.txt
