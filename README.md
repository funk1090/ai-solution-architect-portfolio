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

🚧 Phase 1 in progress — see [docs/architecture/adr](docs/architecture/adr)
for the architecture decisions made so far.

## Repository structure

```
.
├── docs/               # Architecture documentation, ADRs, diagrams
├── datasets/           # Synthetic data (never real/confidential information)
├── backend/            # Backend services (FastAPI, pipelines, etc.)
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
