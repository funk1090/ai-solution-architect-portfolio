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

✅ **Phase 1** — Synthetic Enterprise Document Generator
✅ **Phase 2** — Document Intelligence Pipeline (Apache Airflow)
✅ **Phase 3** — Requirement Intelligence Engine (83.5% accuracy vs. 17.5% baseline)
✅ **Phase 4** — Enterprise AI Knowledge Assistant (local RAG, pgvector + Ollama)
✅ **Phase 5** — Performance Lab (15.3x embedding speedup, ~6.4x ingestion speedup)
✅ **Phase 6** — Document Understanding: Logistic Regression (83.5%) vs.
a neural network (79.0%) compared honestly — the simpler model won,
confirmed rather than assumed.

Only **Phase 7** (Product Hardening) remains.

See [docs/architecture/adr](docs/architecture/adr) for architecture
decisions and [docs/architecture/features](docs/architecture/features)
for feature design documents.

## Quick start

```bash
# 1. Start PostgreSQL (with pgvector) and Airflow
export AIRFLOW_UID=$(id -u)
docker compose up -d postgres airflow

# 2. Generate the synthetic document corpus (Phase 1)
cd backend
uv sync
uv run document-generator generate --document-type rfp --count 10
uv run document-generator generate --document-type excel_requirements --count 20
uv run document-generator generate --document-type technical_manual --count 10

# 3. Ingestion pipeline (Phase 2/5) -- sequential or parallel
cd ingestion_pipeline && uv sync
uv run ingestion-pipeline ingest --parallel

# 4. Classifier: compare Logistic Regression vs. neural network (Phase 3/6)
cd ../requirement_classifier && uv sync
uv run requirement-classifier compare
uv run requirement-classifier classify --text "The system must support 10,000 concurrent users."

# 5. Knowledge assistant (Phase 4/5)
cd ../knowledge_assistant && uv sync
uv run knowledge-assistant index
uv run knowledge-assistant ask --question "What is the budget range mentioned in the proposals?"
```

## Repository structure

```
.
├── docs/               # Architecture documentation, ADRs, diagrams
├── datasets/           # Synthetic data (never real/confidential information)
├── backend/            # Backend services
│   ├── src/document_generator/       # Phase 1: synthetic document generator
│   ├── shared_core/                  # Shared table definitions (ADR-0006)
│   ├── ingestion_pipeline/           # Phase 2/5: extraction pipeline + parallelism
│   ├── requirement_classifier/       # Phase 3/6: classical ML + neural network
│   └── knowledge_assistant/          # Phase 4/5: RAG assistant + benchmarks
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
