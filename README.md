# AI Solution Architect Portfolio

An enterprise-grade AI platform built incrementally as a learning journey
and professional portfolio, using exclusively open-source technologies
and synthetic data.

## Philosophy

- **Open Source First**: self-hostable software is prioritized over
  proprietary cloud services.
- **Learn by Building**: every concept learned from a technical book is
  translated into a real implementation within the platform.
- **Architecture Before Code**: every significant feature is designed
  (problem statement, requirements, diagram, ADR) before implementation.
- **Documentation as Code**: documentation is a deliverable, not an
  afterthought.

## Current status

✅ **Phase 1 complete** — Synthetic Enterprise Document Generator
(Feature 0001): generates fictional RFPs (PDF), technical requirement
matrices (Excel), and technical manuals (PDF), with metadata persisted
to PostgreSQL and integrity verified via SHA-256 checksums.

✅ **Phase 2 complete** — Document Intelligence Pipeline (Feature 0002):
extracts text from PDFs and structured data from Excel matrices,
orchestrated by Apache Airflow. Idempotent (safe to re-run) and
fault-isolated (one bad file never blocks the rest of a batch).

See [docs/architecture/adr](docs/architecture/adr) for architecture
decisions and [docs/architecture/features](docs/architecture/features)
for feature design documents.

## Quick start

```bash
# 1. Start PostgreSQL (app data) and Airflow (orchestration)
export AIRFLOW_UID=$(id -u)
docker compose up -d postgres airflow

# 2. Generate the synthetic document corpus (Phase 1)
cd backend
uv sync
uv run document-generator generate --document-type rfp --count 5
uv run document-generator generate --document-type excel_requirements --count 5
uv run document-generator generate --document-type technical_manual --count 5

# 3. Run the ingestion pipeline (Phase 2) — either directly...
cd ingestion_pipeline
uv sync
uv run ingestion-pipeline ingest

# ...or through Airflow, at http://localhost:8080 (admin/admin),
# DAG: ingest_documents
```

Generated files land in `backend/datasets/generated/<document-type>/`.
Extracted content lands in the `ingested_content` PostgreSQL table.

## Repository structure

```
.
├── docs/               # Architecture documentation, ADRs, diagrams
├── datasets/           # Synthetic data (never real/confidential information)
├── backend/            # Backend services
│   ├── src/document_generator/       # Phase 1: synthetic document generator
│   └── ingestion_pipeline/           # Phase 2: PDF/Excel extraction pipeline
├── frontend/           # User interfaces (when applicable)
├── infrastructure/     # Docker Compose, Airflow, deployment configuration
├── notebooks/          # Exploration and prototyping in Jupyter
├── experiments/        # Proofs of concept that don't reach production
├── tests/              # Automated tests
└── books/              # Notes and summaries from the technical books used
```

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).

## Disclaimer

All business content (RFPs, requirements, datasets) is synthetic and
fictional (fictional company "Andes Digital Networks"). No confidential
or proprietary information is used.
