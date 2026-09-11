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

See [docs/architecture/adr](docs/architecture/adr) for architecture
decisions and [docs/architecture/features](docs/architecture/features)
for feature design documents.

## Quick start

```bash
# 1. Start PostgreSQL
docker compose up -d postgres

# 2. Install dependencies
cd backend
uv sync

# 3. Run tests
uv run pytest -v

# 4. Generate synthetic documents
uv run document-generator generate --document-type rfp --count 5
uv run document-generator generate --document-type excel_requirements --count 5
uv run document-generator generate --document-type technical_manual --count 5
```

Generated files land in `backend/datasets/generated/<document-type>/`.

## Repository structure

```
.
├── docs/               # Architecture documentation, ADRs, diagrams
├── datasets/           # Synthetic data (never real/confidential information)
├── backend/            # Backend services (document generator, future services)
├── frontend/           # User interfaces (when applicable)
├── infrastructure/     # Docker Compose, IaC, deployment configuration
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
