# Feature 0008: Web Frontend

**Status:** Proposed
**Target release:** v0.8.0
**Depends on:** Feature 0007 (Product Hardening: unified API)

## 1. Problem Statement

Everything built in Phases 1-7 is operated through CLIs or raw HTTP calls. A sales engineer at the fictional company *Andes Digital Networks* cannot be expected to use `curl` and an API key to ask "what budget ranges appear in our RFPs?" or to classify a requirement. The platform needs a small web interface that makes the existing capabilities usable and demonstrable, without duplicating any business logic.

The frontend is a **pure client of the Phase 7 API**. It owns presentation only.

## 2. Scope

### In scope
- A Streamlit application with four pages: Corpus, Pipeline, Ask, Classify.
- Two small, backward-compatible API additions needed to support the UI.
- A fix for the per-request embedding-model reload in `/assistant/ask`, with before/after measurement.
- A seventh CI job for the frontend.

### Explicitly out of scope (deferred)
- **Compliance validation (RFP requirements vs. technical manuals) -> Feature 0009.** It is new business logic, not presentation. Also, the current synthetic manuals have no category-aware content, so the feature would answer "no evidence" for almost every requirement. Prerequisite: extend `TechnicalManualGenerator` with correlated content, as ADR-0004 did for RFPs.
- Real user login / multi-user sessions.
- Asynchronous job execution for long operations.

## 3. Requirements

### Functional
| ID | Requirement |
|----|-------------|
| FR1 | Four pages: Corpus, Pipeline, Ask, Classify. |
| FR2 | **Corpus:** show API reachability and counts per document type (generated, ingested, indexed chunks). |
| FR3 | **Pipeline:** trigger generate, ingest (sequential or parallel) and index; show each run's summary. |
| FR4 | **Ask:** show the answer, the `grounded` flag, and sources as document type + file name (not raw checksums). |
| FR5 | **Classify:** classify free text; trigger model comparison and show metrics. |
| FR6 | API additions: `GET /corpus/summary`, and a `source_details` field on `/assistant/ask`. The existing `sources` field is unchanged. |
| FR7 | Load the embedding model once per process instead of once per request; measure before/after. |
| FR8 | CI gains a seventh job running the frontend tests. |

### Non-functional
| ID | Requirement |
|----|-------------|
| NFR1 | The API key lives server-side only (Streamlit process); it never reaches the browser. |
| NFR2 | No business logic in the UI. All calls go through one typed `ApiClient`. |
| NFR3 | `ApiClient` is testable with an injected fake HTTP transport. |
| NFR4 | Visible progress states, configurable timeouts, friendly errors for API unreachable (connection error) and 401. |
| NFR5 | No new infrastructure: no new containers or databases. |

## 4. Architecture

```
Browser --> Streamlit (frontend/, port 8501) --HTTP + X-API-Key--> FastAPI (backend/api, port 8000)
                                                                      |
                                    document_generator / ingestion_pipeline / requirement_classifier / knowledge_assistant
                                                                      |
                                                       PostgreSQL+pgvector, Ollama
```

Layout (at repo root, independent uv project per ADR-0003):

```
frontend/
  pyproject.toml
  src/portfolio_frontend/
    api_client.py     # typed ApiClient + response models, the only place that talks HTTP
    config.py         # API_BASE_URL, API_KEY, timeouts (pydantic-settings)
    app.py            # entrypoint / navigation
    pages/ corpus.py, pipeline.py, ask.py, classify.py   # thin: render + call ApiClient
  tests/
```

`frontend/` sits outside `backend/`, so the uv workspace auto-discovery issue documented in ADR-0003 should not apply. To be verified on `uv init`.

## 5. Design Decisions

1. **Streamlit as a separate process calling the API over HTTP.** The key stays server-side and there is no CORS surface. Python end to end, so it fits the existing toolchain and keeps effort proportional to a portfolio project.
2. **Thin pages + one `ApiClient`.** Pages only render; the client owns URLs, headers, timeouts, error mapping and typed models.
3. **Two small API additions instead of UI workarounds.** A counts endpoint and human-readable source details belong to the backend; computing them in the UI would require DB access or checksum lookups from the client.
4. **Load the embedding model once per process.** Today `ask_assistant` builds the model on every request. Fix with a cached factory (module-level/`lru_cache`), covered by a before/after timing.
5. **Compliance validation deferred** (see Scope) to avoid shipping a feature that mostly answers "no evidence".

## 6. Trade-offs

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Streamlit** | Fastest, pure Python, key stays server-side | Less control over UX; rerun execution model; no built-in login | **Chosen** |
| HTMX + Jinja (served by FastAPI) | One process, light | More hand-written HTML/CSS; mixes UI into the API service | Rejected for now |
| React/Vite SPA | Most flexible, industry-standard | Second toolchain, CORS, key handling problem (needs BFF), much more effort | Rejected for now; revisit if UX becomes the goal |
| Import backend modules / query DB from UI | Fewer hops | Bypasses auth, duplicates logic, couples UI to storage | Rejected |

## 7. Known Limitations
- Streamlit has no login: intended for localhost / trusted network only.
- Long operations (ingest, index, compare) are synchronous; the UI blocks with a spinner until the API responds.
- Sources are only as rich as `document_metadata` allows.

## 8. Testing Strategy
- `ApiClient`: unit tests with `httpx.MockTransport` (success, 401, connection error, timeout, malformed payload).
- Pages: smoke tests with Streamlit `AppTest` against a fake `ApiClient`.
- API additions: tests with in-memory fakes (`/corpus/summary` counts, `source_details` shape, `sources` unchanged).
- FR7: timing of `/assistant/ask` before vs. after, recorded in the implementation notes.
- Manual end-to-end against the live stack (Postgres, Ollama, API, Streamlit).

## 9. Definition of Done (per project standard)
Working implementation, tests, documentation (README, this doc, SYSTEM_OVERVIEW update), architecture diagram, Docker support (Dockerfile for the frontend; compose entry optional), example usage, CI job green, release notes v0.8.0.

---

## Implementation Notes (added after building)

### What was built
- `frontend/` (seventh independent uv project): Streamlit app with a single typed `ApiClient` and four pages (Corpus, Pipeline, Ask, Classify).
- API (v0.8.0): `GET /corpus/summary`, `source_details` on `POST /assistant/ask` (existing `sources` unchanged), and the embedding model loaded once per process via a cached factory (`portfolio_api/dependencies.py`).
- CI: seventh job (`frontend`). Tests: 12 in `backend/api` (8 new), 16 in `frontend`.

### Deviations from the design
- Pages live in `views/` (not `pages/`) so Streamlit does not auto-detect them as its own multipage entries; navigation is a sidebar radio instead of `st.navigation`. Same behaviour, simpler to test: each page is a `render(client)` function.
- `frontend/` did not trigger the uv workspace auto-discovery issue from ADR-0003 (it lives outside `backend/`), as predicted.

### Bugs found and fixed while building
1. **Unauthenticated requests reached the database.** The first version of `/corpus/summary` read the counts in a FastAPI dependency. FastAPI keeps resolving other dependencies after a validation error (missing `X-API-Key` -> 422), so the database query ran for unauthenticated callers. Found by a unit test that replaced the reader with a function that fails if called. Fix: the dependency now returns the reader without calling it; the endpoint calls it after authentication has passed.
2. **Flaky page tests.** `AppTest` has a 3 s default timeout; one run failed once and then passed three times in a row. Raised to 30 s so slow machines and cold CI runners do not fail spuriously.

### FR7 measurement (embedding model loaded once)
Measured against the real stack (RTX 5080, llama3 on Ollama), same question asked twice per version:

| Version | 1st call | 2nd call | Embedding model loaded |
|---|---|---|---|
| v0.7.0 (before) | 12.0 s | 4.5 s | on every request (log shows `Loading weights` before each) |
| v0.8.0 (after) | 18.7 s | 1.9 s | once (log shows it only before the first request) |

The log evidence is conclusive. The timings are indicative only: n=1, the LLM writes a different answer each time, and the "after" run happened first, so its first call also absorbed Ollama's cold start. What the numbers do support: the warm call went from 4.5 s to 1.9 s.

### Finding: classifier on short text
The Classify page labelled "The system must encrypt all data using AES-256." as *Compliance*, while the longer sentence validated in Phase 3 ("... and enforce strict access controls.") is labelled *Security*. Confirmed directly against the API (not a frontend issue). With ~83% cross-validated accuracy on synthetic data, short or ambiguous text can land in a neighbouring category. The page now carries a caption saying so and uses the representative sentence as its example.

### Finding: stale index
`/corpus/summary` showed 240 ingested documents but only 20 indexed chunks, because the last indexing run predated most ingestion. The Corpus page now warns when documents are ingested but nothing is indexed; re-indexing is one click on the Pipeline page. (Surfacing this is exactly the reason to have a status page.)

### Known limitations (unchanged from design, now observed)
- No login: localhost only. Long operations (index, compare) block with a spinner.
- Compliance validation remains deferred to Feature 0009.
