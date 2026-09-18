# ADR-0006: Shared schema package for cross-module table definitions

## Status
Accepted

## Context
Three independent uv projects (ADR-0003) now each maintain their own
hand-written SQLAlchemy declarative definitions of the
`document_metadata` and/or `ingested_content` tables:

- `document_generator` owns and writes `document_metadata`.
- `ingestion_pipeline` reads `document_metadata` (read-only) and owns
  `ingested_content`.
- `requirement_classifier` reads `ingested_content` (read-only).

This duplication was accepted deliberately in ADR-0003 as a documented
trade-off, with an explicit trigger condition: "if a third module needs
the same schema, this duplication should be resolved." That condition
has now been met twice over (both tables are duplicated across three
modules). Left unresolved, every future schema change requires
remembering to update every duplicate by hand — a silent-drift risk
that grows with each new module.

## Decision
Extract a new, minimal internal package, `backend/shared_core/`,
containing **only** the SQLAlchemy declarative table definitions for
`document_metadata` and `ingested_content` — no business logic, no
Pydantic domain models, no read/write policy. Each of the three
existing modules depends on it via a `uv` local editable path
dependency (`uv add --editable ../shared_core`).

Following the standing procedure established in ADR-0003,
`shared_core` is added to `backend/pyproject.toml`'s
`[tool.uv.workspace]` `exclude` list immediately after its `uv init`,
before any other `uv` command runs against it.

`shared_core`'s declarative base uses the function-based
`declarative_base()`, not the SQLAlchemy 2.0-only `DeclarativeBase`
class — required for compatibility with the older SQLAlchemy version
pinned inside the Airflow container's constraints file (see ADR-0003's
Feature 0002 implementation notes), since `ingestion_pipeline` imports
this package from within that environment.

## Alternatives considered

**Do nothing (accept the duplication)**
- Advantages: zero migration work.
- Disadvantages: the risk this ADR exists to address was already
  flagged twice as unsustainable; a third module hitting the same
  duplication is the point at which "revisit later" stops being a
  reasonable answer.

**Merge everything into a single monolithic backend project**
- Advantages: no cross-project dependency wiring needed at all.
- Disadvantages: reverses the module isolation validated across three
  real features (ADR-0003) — unrelated dependencies (Faker/fpdf2 vs.
  pdfplumber/pandas vs. scikit-learn) would mix again for no reason
  other than avoiding a small dependency-wiring exercise.

**Share full repository classes, not just table definitions**
- Advantages: even less duplicated code.
- Disadvantages: each module's repository intentionally has a
  different access policy around the same tables (e.g.,
  `ingestion_pipeline`'s read-only view of `document_metadata` vs.
  `document_generator`'s full read/write access). Sharing the
  repository layer, not just the schema, would recouple decisions that
  were deliberately kept separate per module.

## Consequences
- A schema change now happens in exactly one file, and every module
  importing it stays in sync automatically — no more hand-copying a
  changed column across three repositories.
- Introduces `uv` local editable path dependencies as a new, standing
  mechanism in this monorepo, alongside the existing workspace-exclude
  pattern.
- `shared_core` has no business behavior and should stay that way — a
  schema-only package is inherently low-churn, which is the right
  property for something three other projects depend on.
- Each module's own Pydantic domain models (`DocumentMetadata` in
  document_generator, `TrainingExample` in requirement_classifier,
  etc.) are unaffected — only the SQLAlchemy table layer is shared.

## References
- ADR-0003: Module structure for Phase 2 (the trigger condition this
  ADR resolves, and the standing workspace-exclude procedure reused
  here).
- Feature 0002's Implementation Notes (the `declarative_base()`
  compatibility constraint imposed by Airflow's constraints file).
