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

✅ **Phase 1 complete** — Synthetic Enterprise Document Generator:
RFPs, technical requirement matrices, and technical manuals.

✅ **Phase 2 complete** — Document Intelligence Pipeline: PDF/Excel
extraction, orchestrated by Apache Airflow.

✅ **Phase 3 complete** — Requirement Intelligence Engine: a text
classifier, **83.5% accuracy vs. a 17.5% baseline**.

✅ **Phase 4 complete** — Enterprise AI Knowledge Assistant: a local
RAG pipeline (pgvector + Ollama), GPU-accelerated, with built-in
anti-hallucination guarantees.

✅ **Phase 5 complete** — Performance Lab: measured, evidence-based
optimizations — **15.3x faster embedding generation** (batching) and
**~6.4x faster ingestion** (multiprocessing across CPU cores).

See [docs/architecture/adr](docs/architecture/adr) for architecture
decisions and [docs/architecture/features](docs/architecture/features)
for feature design documents.

## Quick start

```bash
# 1. Start PostgreSQL (with pgvector) and Airflow
export AIRFLOW_UID=$(id -u)
docker compose up -d postgres airflow
# Ollama: point knowledge_assistant's config at any running Ollama
# instance (localhost:11434 by default).

# 2. Generate the synthetic document corpus (Phase 1)
cd backend
uv sync
uv run document-generator generate --document-type rfp --count 10
uv run document-generator generate --document-type excel_requirements --count 20
uv run document-generator generate --document-type technical_manual --count 10

# 3. Run the ingestion pipeline (Phase 2) -- sequential or parallel (Phase 5)
cd ingestion_pipeline && uv sync
uv run ingestion-pipeline ingest
uv run ingestion-pipeline ingest --parallel   # Phase 5: multiprocessing

# 4. Train and use the requirement classifier (Phase 3)
cd ../requirement_classifier && uv sync
uv run requirement-classifier train
uv run requirement-classifier classify --text "The system must support 10,000 concurrent users."

# 5. Index and query the knowledge assistant (Phase 4)
cd ../knowledge_assistant && uv sync
uv run knowledge-assistant index
uv run knowledge-assistant ask --question "What is the budget range mentioned in the proposals?"

# 6. Benchmark performance (Phase 5)
uv run knowledge-assistant benchmark-embeddings
cd ../ingestion_pipeline && uv run ingestion-pipeline benchmark
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
│   ├── requirement_classifier/       # Phase 3: requirement category classifier
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
