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
- **Update (implementation note)**: placing `ingestion_pipeline/` as a
  subdirectory of `backend/` caused `uv` to auto-detect it as a
  workspace member and share `backend/.venv` between both projects,
  actively uninstalling `document-generator`'s own dependencies during
  `ingestion_pipeline`'s `uv sync` — the opposite of the isolation this
  ADR intends. Fixed by adding `[tool.uv.workspace]` with an `exclude`
  entry for `ingestion_pipeline` in `backend/pyproject.toml`, forcing
  `uv` to treat it as a fully independent project despite the nested
  path.
- **Update (recurrence + standing procedure)**: the exact same
  auto-discovery issue recurred when `requirement_classifier/` (Feature
  0003) was created — `uv init` printed `Adding requirement-classifier
  as member of workspace` immediately, and a `members` entry
  reappeared in `backend/pyproject.toml`'s `[tool.uv.workspace]`
  alongside the `exclude` list, contradicting it. Two occurrences make
  this a standing procedure, not a one-off fix: **immediately after
  running `uv init` for any new module under `backend/`, check the
  command's own output for "Adding \<name\> as member of workspace".**
  If it appears, before running any other `uv` command (`uv add`, `uv
  sync`), open `backend/pyproject.toml` and ensure the new module's
  name is listed under `[tool.uv.workspace]` `exclude` and is **not**
  present anywhere under a `members` list — delete any `members` entry
  entirely if one exists, since `exclude` and `members` for the same
  package name is a contradiction `uv` does not reliably resolve.
- The `document_metadata`/`ingested_content` table schemas are now
  duplicated across **three** independent modules
  (`ingestion_pipeline`, `requirement_classifier`, and
  `document_generator` for its own table). This is the trigger
  condition this ADR originally flagged for extracting a shared
  internal package — deliberately still deferred (see Feature 0003's
  Future Improvements) rather than introducing a new cross-project
  dependency mechanism under time pressure. This should be the first
  architecture task of the next dedicated session, not deferred a
  third time.
- Each module keeps its own `datasets/` output location relative to
  itself, consistent with the `**/datasets/generated/` gitignore
  pattern already in place.

## References
- ADR-0001: Repository strategy (monorepo) — the deferred decision this
  ADR resolves.
- Fundamentals of Data Engineering (Reis & Housley) — Ch. 3, Designing
  Good Data Architecture (bounded, single-responsibility components).
