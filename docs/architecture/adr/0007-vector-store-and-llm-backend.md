# ADR-0007: Vector store and LLM backend choice (pgvector + Ollama)

## Status
Accepted

## Context
Feature 0004 introduces two entirely new categories of infrastructure
to the platform: vector similarity search (to retrieve relevant text
chunks) and local LLM inference (to generate grounded answers). Both
choices have significant, hard-to-reverse consequences for operational
complexity, so they warrant their own ADR rather than living only in
Feature 0004's trade-off table.

## Decision

**Vector storage**: the `pgvector` PostgreSQL extension, added to the
same PostgreSQL instance already running `document_metadata` and
`ingested_content`. This requires switching the `postgres` service's
Docker image to one with `pgvector` pre-installed (e.g.,
`pgvector/pgvector:pg16`) rather than the plain `postgres:16-alpine`
image used until now.

**LLM inference**: Ollama, reusing the instance already running on the
developer's machine (`localhost:11434`, outside this project's own
`docker-compose.yml`) rather than starting a second, conflicting
container on the same port. The already-downloaded `llama3:latest`
(8B parameters, 4.7 GB) is used as the initial model — larger than the
1B-3B range originally envisioned, but avoiding a redundant download of
infrastructure that already exists is a better trade than optimizing
prematurely for inference speed. Swapping to a smaller model later, if
latency becomes a problem, is a one-line configuration change thanks to
the Factory pattern (Feature 0004, Design Decision 6).

**Portability**: vector storage is accessed exclusively through a
`VectorStoreRepository` interface (the same Repository pattern used
throughout this codebase — `DocumentMetadataRepository`,
`IngestedContentRepository`, etc.), with `PgVectorRepository` as its
only implementation for now. Chunking, embedding generation, retrieval
orchestration, prompt construction, and LLM invocation depend only on
this interface, never on `pgvector`-specific code. Switching to a
dedicated vector database later means writing one new implementation
of this interface and changing one configuration value — not a
pipeline redesign. This does not make a future migration free: existing
embeddings would still need to be exported and re-inserted into the new
store, and any vendor-specific feature (e.g., hybrid search) not
captured by the interface would require deliberately extending it.

## Alternatives considered

**Dedicated vector database (Milvus, Weaviate, Qdrant)**
- Advantages: purpose-built for vector search at scale, richer indexing
  options, better performance at very large corpus sizes.
- Disadvantages: an entirely new service to run, operate, and back up,
  for a corpus currently measured in hundreds of documents — the kind
  of infrastructure that solves a scale problem this project doesn't
  have yet, echoing the same "avoid overengineering" reasoning already
  applied in ADR-0005 (choosing joblib over MLflow).

**Hosted LLM API (OpenAI, Anthropic, etc.) instead of Ollama**
- Advantages: substantially higher answer quality without local
  hardware constraints.
- Disadvantages: violates "Open Source First" and the project's
  self-hosted constraint (see Constraints), introduces per-call cost,
  and creates an external dependency the rest of the platform
  deliberately avoids.

**A larger local model, downloaded specifically for this project**
- Advantages: potentially better answer quality than reusing whatever
  happened to already be available.
- Disadvantages: downloading a new multi-gigabyte model when a working
  one (`llama3:latest`) is already present on the machine, just to hit
  an arbitrary size target, is wasted bandwidth and disk space for no
  concrete benefit yet. The factory pattern keeps this decision
  reversible — see Consequences.

## Consequences
- The `postgres` Docker image changes for the first time since Phase 1
  — existing `document_metadata`/`ingested_content` data is unaffected
  (same underlying Postgres, just an image with an added extension),
  but this must be verified explicitly during implementation, not
  assumed.
- `docker-compose.yml` still defines an `ollama` service, so a fresh
  clone of this repository with no pre-existing Ollama instance can run
  the full stack out of the box. On this particular development
  machine, that service is deliberately **not started**, since it would
  conflict with an already-running standalone `ollama` container bound
  to the same host port (`11434`) from another project. The
  application is configured to reach Ollama at `localhost:11434`
  regardless of which container is actually serving it — the two are
  interchangeable from the application's point of view.
- Retrieval quality and answer quality are both capped by the
  relatively small embedding model and the general-purpose (not
  fine-tuned) LLM chosen. This is acceptable for a portfolio-scale
  demonstration of the RAG pattern itself; revisit if a real production
  use case demands better quality.

## References
- Feature 0004: Enterprise AI Knowledge Assistant.
- ADR-0005: ML model evaluation and persistence strategy (the
  "avoid overengineering relative to current scale" reasoning reused
  here for vector storage).
- Project Constraints: "No cloud dependencies unless explicitly
  requested"; "Development performed on personal hardware."
