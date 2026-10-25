# Feature 0010: Containerized Deployment and API Rate Limiting

**Status:** Implemented
**Target release:** v0.9.0 (together with Feature 0009 and the project closure)
**Depends on:** Feature 0007 (unified API), Feature 0008 (frontend), Feature 0009 (compliance)

## 1. Problem Statement

Today the platform runs from several terminals: `docker compose up` brings up PostgreSQL, Ollama and Airflow, but the API (`uvicorn`) and the frontend (`streamlit`) are started by hand inside `uv` environments. A reviewer cloning the repository cannot get the system running with minimal effort, which breaks the project principle *Reproducibility* ("clone the repository and start the platform with minimal effort"). Docker support for the API and the frontend was part of the Definition of Done of Feature 0008 and was not delivered.

Separately, the API exposes endpoints that are expensive (LLM calls, embeddings, ingestion). Nothing prevents a client from saturating the GPU or the process with repeated calls. The project principle *Security by Design* asks for secure defaults.

## 2. Scope

### In scope
- A Dockerfile for the API and one for the frontend (separate images, built from the repository root).
- Compose services `api` and `frontend`, wired to the existing `postgres`.
- Compose profiles so that the default `docker compose up` starts only what the application needs.
- Secrets and configuration through environment variables; no secret has a default in the compose file.
- API rate limiting, with per-tier limits and a friendly message in the frontend.
- An end-to-end smoke check script, run locally and in CI.
- Documentation, architecture diagram of the final system, Future Work section, release notes v0.9.0.

### Explicitly out of scope
- Kubernetes / Helm, TLS termination and reverse proxy, login for Streamlit.
- Distributed rate limiting (Redis), asynchronous job execution.
- Observability stack (Grafana dashboards): listed as future work.

## 3. Requirements

### Functional
| ID | Requirement |
|----|-------------|
| FR1 | `docker compose up -d` (with a configured `.env`) starts PostgreSQL, the API and the frontend, healthy and connected. |
| FR2 | Optional profiles: `ollama` (containerized LLM, GPU reservation) and `airflow` (orchestration). |
| FR3 | The API container reaches Ollama through a configurable URL (host or container). |
| FR4 | Rate limiting with two tiers: *expensive* (`/assistant/ask`, `/compliance/check`, pipeline operations, classifier comparison) and *default* (everything else). Exceeding a limit returns HTTP 429 with `Retry-After`. |
| FR5 | Limits are configurable through environment variables; `0` disables a tier. |
| FR6 | The frontend shows "rate limit reached, retry in N seconds" on 429. |
| FR7 | A smoke script verifies: health, 401 without key, 200 with key, 429 after exceeding a (low) limit. |
| FR8 | CI builds both images and runs the smoke script against the stack without Ollama. |

### Non-functional
| ID | Requirement |
|----|-------------|
| NFR1 | Secrets are never baked into images. `API_KEY` is mandatory (`${API_KEY:?...}`); compose fails fast if it is missing. |
| NFR2 | Containers run as a non-root user; published ports bind to `127.0.0.1`. |
| NFR3 | Services declare healthchecks; `depends_on` uses `service_healthy`. |
| NFR4 | The embedding model is available offline after the build (baked into the API image). |
| NFR5 | The rate limiter is unit-testable with an injected clock and has bounded memory. |

## 4. Architecture

```
                 127.0.0.1:8501                 127.0.0.1:8000
Browser  ---->  frontend (Streamlit) --HTTP+X-API-Key--> api (FastAPI)
                                                          |  rate limiter (after auth)
                                         +----------------+------------------+
                                         v                                   v
                                   postgres (pgvector)        Ollama (host.docker.internal:11434
                                                              existing GPU container, or `ollama` profile)
Optional profile `airflow`: airflow + airflow-postgres (unchanged)
```

Layout:

```
backend/api/Dockerfile        # multi-stage, uv, CPU-only torch, model baked in
frontend/Dockerfile           # slim image, no torch
.dockerignore
.env.example                  # repository root: API_KEY, POSTGRES_*, OLLAMA_BASE_URL, limits
docker-compose.yml            # + api, frontend; profiles for ollama and airflow
scripts/smoke.sh
backend/api/src/portfolio_api/rate_limit.py
```

## 5. Design Decisions

1. **One image per service, build context at the repository root.** The API depends on several sibling packages (monorepo, ADR-0003), so its context must see them. The frontend image stays small because it never installs `torch`.
2. **CPU-only `torch` in the API image.** Embeddings of short texts do not need the GPU; the CUDA wheels would add gigabytes. The GPU is reserved for the LLM.
3. **Embedding model baked into the image** (downloaded at build time). The first request does not depend on the network; the cost is ~90 MB of image size.
4. **Ollama is reached through `OLLAMA_BASE_URL`; a compose profile provides it for fresh setups.** Evidence from the author's machine: Ollama already runs as a standalone Docker container (`ollama`, port 11434) using the GPU (RTX 5080 Laptop, Docker Desktop on WSL2), so GPU passthrough to containers works. The default `OLLAMA_BASE_URL` is `http://host.docker.internal:11434`, which reuses that running container and its downloaded model (no re-download). The compose `ollama` service (today CPU-only, no GPU reservation) moves to the `ollama` profile and gains an NVIDIA device reservation, so a new user can get a fully self-contained stack with `--profile ollama`. Note: the profile service and a manually started container cannot both publish port 11434; the README documents this.
5. **Profiles change the meaning of plain `docker compose up`.** Today it also starts `ollama` and `airflow`. After this feature those require `--profile ollama` / `--profile airflow`. This is a deliberate, documented behavior change: the default demo is lighter and Airflow (standalone mode) is heavy.
6. **Secrets by environment, mandatory and without defaults.** The existing Postgres credentials (`portfolio/portfolio`) remain as local-development defaults; they are documented as such and ports are bound to localhost.
7. **Rate limiter: in-process token bucket as a FastAPI dependency, applied after authentication.** Key = the authenticated API key. Because there is a single shared key today, the limit is effectively *global*: it protects the GPU/LLM from saturation, which is the real risk. Applying it after authentication keeps memory bounded (only valid keys create buckets) and means unauthenticated 422/401 requests never reach it. Metrics: a Prometheus counter `api_rate_limited_total{tier}`.
8. **Smoke test in CI without Ollama**, exercising only endpoints that do not call the LLM, plus a low limit configured for the test to provoke a 429.

## 6. Trade-offs

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **Docker Compose with profiles** | Simple, reproducible, fits the project size | Single host only | **Chosen** |
| Kubernetes / Helm | Production-standard | Large effort, no benefit for a single-host demo | Future work |
| Ollama in the default stack | Self-contained | Large model download on first start; port clash with an existing Ollama | Optional profile (`ollama`) |
| **In-memory rate limiter** | No new infrastructure, small, testable | Per process; limits multiply with several workers | **Chosen** (documented) |
| Redis-based limiter | Correct across workers | New container and dependency | Rejected for now |
| Rate limiting at a reverse proxy | Decoupled from the app | New component to configure and test | Rejected for now |
| `slowapi` | Ready-made | Extra dependency, less control over keying and clock injection | Rejected |
| Downloading the model at runtime | Smaller image | First request needs network; flaky offline | Rejected |

## 7. Known Limitations
- The limiter is per process and, with a single API key, effectively global. It does not slow down brute-force attempts with wrong keys (a failed-auth throttle by IP is future work).
- Streamlit still has no login; ports are bound to `127.0.0.1` for that reason.
- Behind a proxy the client IP would be wrong; this design does not depend on the IP.
- Long operations remain synchronous.

## 8. Testing Strategy
- Limiter: unit tests with a fake clock (burst, refill, per-tier isolation, disabled tier, bounded memory).
- API: `TestClient` tests for 429 + `Retry-After`, tiers applied to the right routes, and that a 422/401 request does not consume tokens.
- Frontend: `ApiClient` maps 429 to a typed error; `AppTest` shows the message.
- `docker compose config` validated in CI; both images built in CI.
- Smoke script (FR7) run locally and in CI.
- Manual end-to-end with host Ollama: Ask and Compliance pages through the containerized stack.

## 9. Open Items to Verify During Implementation
- How the database schema is created on a fresh volume (the API must not start against an empty database without tables).
- Whether the API already exposes a health endpoint suitable for the container healthcheck.
- How the sibling packages are declared as dependencies (path dependencies vs. workspace), which determines the Dockerfile `COPY` and `uv sync` steps.
- Data directory configuration (`datasets/`) so pipeline operations work from inside the container.

## 10. Definition of Done
Working implementation, unit tests, documentation (README quick start with Docker, this document, SYSTEM_OVERVIEW update), architecture diagram of the final system, Dockerfiles and compose, example `.env`, smoke script green locally and in CI, release notes v0.9.0, Future Work section.


---

# Implementation Notes (Feature 0010)

**Status:** Implemented and validated against the real stack (2026-10-24). CI `docker` job: see the v0.9.0 release notes.
**Release:** v0.9.0 (bundled with Feature 0009).

## What was built

- **Rate limiter** (`portfolio_api/rate_limit.py`): token bucket per API key, in process, thread-safe, LRU-bounded (1024 keys), injectable clock. Two FastAPI dependencies, both built on `verify_api_key` (which now returns the key): `limit_default` is attached to every router in `main.py`; `limit_expensive` is added on six routes (`/assistant/index`, `/assistant/ask`, `/compliance/check`, `/classifier/compare`, `/documents/generate`, `/ingestion/run`). `/health` and `/metrics` are outside it. Settings: `rate_limit_default_per_minute` (120) and `rate_limit_expensive_per_minute` (10); `0` disables a tier.
- **Frontend**: `ApiRateLimited` (carries `retry_after`) and a single `_raise_for_status` used by every request path.
- **Images**: `backend/api/Dockerfile` (locked dependencies via `uv export`, without the `nvidia-*`/`triton` packages, CPU torch through `--torch-backend cpu`, embedding model baked in, non-root, healthcheck) and `frontend/Dockerfile` (`uv sync --frozen`, no torch). Build context is the repository root; `.dockerignore` keeps `.venv`, `.env`, tests and datasets out.
- **Compose**: `api` and `frontend` services; `ollama` and `airflow` moved to profiles; Postgres published on `127.0.0.1`; `API_KEY` required (`${API_KEY:?...}`); `host.docker.internal` mapped for Linux hosts; documents live in a named volume.
- **Smoke test**: `scripts/smoke.sh` (health, 422 without key, 401 with a wrong key, 200 with the key, frontend health, optional 429). CI job `docker` builds the stack without Ollama and runs it with a limit of 5 per minute.

## Measured / observed

| Item | Result |
|---|---|
| Rate limit over HTTP (limit 3 per minute) | `200 200 200 429 429` |
| API image build (cold) | about 2 minutes; 3.99 GB |
| Frontend image build | about 30 seconds; 1.28 GB |
| Stack start (`up --wait`) | all three services healthy in under 20 s once built |
| `scripts/smoke.sh` | 5/5 checks pass |
| Compliance through the containerized stack | same verdicts as the CLI; the container reaches the GPU Ollama via `host.docker.internal` |

## Decisions that held, and a correction

- The design listed GPU passthrough to Docker as an unverified risk. It was not: Ollama already ran as a GPU container on the author's machine, so the design now treats it as available and keeps Ollama out of the default stack only because it is shared with another project.
- The tier wiring test originally inspected FastAPI route internals; that broke on a newer FastAPI (lazy included routers). It was replaced by a source scan plus behavioural tests, which do not depend on framework internals.
- A request that fails body validation (422) still consumes a rate-limit token (FastAPI resolves dependencies before reporting body errors), whereas missing or wrong credentials (422/401) do not. Only authenticated clients can spend tokens.

## Not validated

- Generate / ingest / index from inside the containers on an empty database. Existing rows hold host paths, so ingesting old documents from a container would fail; a clean volume should work but was not exercised.
- GPU reservation of the `ollama` profile service (the author uses an existing Ollama container).
- The `docker` CI job on a cold runner (build time and Hugging Face download).

## Known limitations

- The limiter is per process; with one shared key it is effectively global. No throttling of failed authentication.
- The frontend has no login; hence the `127.0.0.1` bindings.
- The API image is large (3.99 GB) because the whole monorepo and its ML dependencies are installed.
