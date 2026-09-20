# AI Solution Architect Portfolio

An enterprise-grade AI platform built incrementally as a learning journey
and professional portfolio, using exclusively open-source technologies
and synthetic data. **All seven phases of the original roadmap are
complete.**

## Philosophy

- **Open Source First**: self-hostable software is prioritized over
  proprietary cloud services.
- **Learn by Building**: every concept learned from a technical book is
  translated into a real implementation within the platform.
- **Architecture Before Code**: every significant feature is designed
  (problem statement, requirements, diagram, ADR) before implementation.
- **Documentation as Code**: documentation is a deliverable, not an
  afterthought.

## Current status — roadmap complete

See [`docs/architecture/SYSTEM_OVERVIEW.md`](docs/architecture/SYSTEM_OVERVIEW.md)
for the full picture of how all seven phases fit together.

| Phase | What it proved | Real result |
|---|---|---|
| 1 — Document Generator | Realistic synthetic data generation | 3 document types, category-correlated text |
| 2 — Ingestion Pipeline | Orchestrated extraction (Apache Airflow) | Idempotent, fault-isolated |
| 3 — Requirement Classifier | Classical ML on real extracted content | 83.5% accuracy vs. 17.5% baseline |
| 4 — Knowledge Assistant | Local, self-hosted RAG | GPU-accelerated, verified anti-hallucination |
| 5 — Performance Lab | Evidence-based optimization | 15.3x / ~6.4x measured speedups |
| 6 — Document Understanding | Honest model comparison | Simpler model won — confirmed, not assumed |
| 7 — Product Hardening | Unified, authenticated, observable API | 6/6 CI jobs green, validated over real HTTP |

## Quick start

```bash
# 1. Start PostgreSQL (with pgvector) and Airflow
export AIRFLOW_UID=$(id -u)
docker compose up -d postgres airflow
# Point knowledge_assistant/api at any running Ollama instance
# (localhost:11434 by default).

# 2. Generate the synthetic document corpus (Phase 1)
cd backend
uv sync
uv run document-generator generate --document-type rfp --count 10
uv run document-generator generate --document-type excel_requirements --count 20
uv run document-generator generate --document-type technical_manual --count 10

# 3. Ingest (Phase 2/5)
cd ingestion_pipeline && uv sync
uv run ingestion-pipeline ingest --parallel

# 4. Classify (Phase 3/6)
cd ../requirement_classifier && uv sync
uv run requirement-classifier compare

# 5. Index and query the knowledge assistant (Phase 4/5)
cd ../knowledge_assistant && uv sync
uv run knowledge-assistant index

# 6. Run everything behind one authenticated API (Phase 7)
cd ../api && uv sync
cp .env.example .env   # set a real API_KEY
uv run uvicorn portfolio_api.main:app --port 8000

curl http://localhost:8000/health
curl -X POST http://localhost:8000/assistant/ask \
  -H "X-API-Key: <your key>" -H "Content-Type: application/json" \
  -d '{"question": "What is the budget range mentioned in the proposals?"}'
```

## Repository structure

```
.
├── .github/workflows/   # CI: one job per module (Phase 7)
├── docs/                # Architecture documentation, ADRs, diagrams
│   └── architecture/SYSTEM_OVERVIEW.md   # Start here
├── datasets/            # Synthetic data (never real/confidential information)
├── backend/             # Six independent uv projects
│   ├── src/document_generator/       # Phase 1
│   ├── shared_core/                  # Shared table definitions (ADR-0006)
│   ├── ingestion_pipeline/           # Phase 2/5
│   ├── requirement_classifier/       # Phase 3/6
│   ├── knowledge_assistant/          # Phase 4/5
│   └── api/                          # Phase 7: unifies all of the above
├── infrastructure/      # Docker Compose, Airflow configuration
└── frontend/            # Not yet built -- see SYSTEM_OVERVIEW's Future Improvements
```

## License

This project is distributed under the MIT License. See [LICENSE](LICENSE).

## Disclaimer

All business content (RFPs, requirements, datasets) is synthetic and
fictional (fictional company "Andes Digital Networks"). No confidential
or proprietary information is used.
