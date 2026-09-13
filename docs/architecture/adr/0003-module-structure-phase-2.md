# ADR-0003: Module structure for Phase 2 (independent uv project)

## Status
Accepted

## Context
ADR-0001 established a monorepo strategy but deferred the question of how
multiple Python modules within `backend/` should be structured once a
second module was needed — noting it would be revisited "when a specific
component reaches enough maturity." Phase 2 (Document Intelligence
Pipeline) is that moment.

The `document-generator` module (Feature 0001) depends on Faker, fpdf2,
and openpyxl for content generation. The ingestion pipeline needs a
different set of libraries (PDF text extraction, Excel row parsing) and
serves a distinct responsibility: reading what Feature 0001 wrote, not
generating new synthetic content.

## Decision
The ingestion pipeline is implemented as an **independent uv project**
at `backend/ingestion_pipeline/`, with its own `pyproject.toml`, its own
virtual environment, and its own `src/ingestion_pipeline/` package —
structurally a sibling of `backend/` (the document-generator project),
not a subdirectory inside it.

## Alternatives considered

**Single shared uv project for all of `backend/`**
- Advantages: one virtual environment to manage, no duplicated
  boilerplate (pyproject.toml, conftest, etc.) per module.
- Disadvantages: dependency lists from unrelated modules mix together
  (Faker and fpdf2 have no reason to be installed when only running the
  ingestion pipeline), and it becomes unclear which module "owns" which
  code as the project grows toward Phase 3 and beyond.

**Independent uv project per module**
- Advantages: clean dependency isolation, each module can be tested,
  versioned, and eventually deployed independently, and the boundary
  matches how a real multi-service backend would be structured.
- Disadvantages: some inevitable duplication (e.g., both projects need
  to know the shape of the `document_metadata` table to read/write it),
  and slightly more repetitive setup (two `pyproject.toml` files, two
  `uv sync` commands) when working across modules.

## Consequences
- Running the ingestion pipeline's tests or CLI requires `cd
  backend/ingestion_pipeline && uv sync` separately from the generator's
  `backend/uv sync` — this is an accepted, documented cost of the
  isolation benefit.
- The `document_metadata` table schema is currently duplicated (as a
  read-only SQLAlchemy model) between the two projects. If a third
  module needs the same schema, this duplication should be resolved by
  extracting a shared internal package (e.g., `backend/shared_core/`)
  — tracked here as a trigger condition for a future ADR, not solved
  preemptively (avoiding speculative generality).
- Each module keeps its own `datasets/` output location relative to
  itself, consistent with the `**/datasets/generated/` gitignore
  pattern already in place.

## References
- ADR-0001: Repository strategy (monorepo) — the deferred decision this
  ADR resolves.
- Fundamentals of Data Engineering (Reis & Housley) — Ch. 3, Designing
  Good Data Architecture (bounded, single-responsibility components).
