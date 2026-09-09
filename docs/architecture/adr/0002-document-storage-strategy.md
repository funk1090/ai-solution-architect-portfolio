# ADR-0002: Document storage strategy (filesystem + PostgreSQL metadata)

## Status
Accepted

## Context
The Synthetic Enterprise Document Generator (Feature 0001) produces
binary files (PDF, XLSX) that need to be both stored durably and
queryable by metadata (type, related fictional entity, generation date,
checksum) for later phases such as the ingestion pipeline and the RAG
knowledge assistant.

Two storage strategies were considered:

1. **Files on the local filesystem, with only metadata stored in
   PostgreSQL** (path, checksum, type, timestamps, etc.).
2. **Documents stored as BLOBs directly inside PostgreSQL**, with no
   separate filesystem artifact.

## Decision
Generated documents are written to the local filesystem under
`datasets/generated/<document-type>/`, and PostgreSQL stores only the
**metadata** describing each file (not its binary content), including
its path and SHA-256 checksum for integrity verification.

## Alternatives considered

**Database BLOBs**
- Advantages: a single source of truth, simpler backup story (one
  database dump captures everything), no risk of "orphaned" files whose
  database record was deleted or vice versa.
- Disadvantages: PostgreSQL is not optimized for large binary object
  storage at scale — it bloats the database size, slows down backups and
  replication, and is a well-known anti-pattern once volumes grow beyond
  a few thousand documents. It also blocks a natural future migration
  path toward object storage (S3/MinIO), which is how this would be
  built in a real production environment.

**Filesystem + metadata in PostgreSQL**
- Advantages: keeps the database small and fast, mirrors how real
  enterprise document management systems are built (metadata store +
  object/file store), and creates a clean seam for later replacing the
  local filesystem with an S3-compatible store (MinIO) without touching
  the metadata schema.
- Disadvantages: introduces the possibility of drift between the
  filesystem and the database (a file deleted manually without updating
  its record, or vice versa). This is mitigated by NFR6 (checksum
  verification) and by treating the generator as the single writer of
  both the file and its metadata record within the same operation.

## Consequences
- A `DocumentMetadataRepository` abstraction is required (see Feature
  0001, Design Decision 2) so that the persistence mechanism can evolve
  (e.g., swapping the local filesystem for MinIO) without changing
  business logic.
- Backup strategy for this project must consider two artifacts, not one:
  the `datasets/` directory and the PostgreSQL database. This is
  acceptable for a personal portfolio project; it would need explicit
  documentation (and likely automation) if this were a real production
  system.
- Any future migration to object storage (MinIO/S3) should update only
  the repository implementation, not the generators or the database
  schema — validating that the abstraction boundary was drawn in the
  right place.

## References
- Fundamentals of Data Engineering (Reis & Housley) — Ch. 5, The Data
  Engineering Lifecycle: Storage.
- Feature 0001: Synthetic Enterprise Document Generator.
