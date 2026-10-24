# Feature 0009: Compliance Validation

**Status:** Proposed
**Target release:** v0.9.0
**Depends on:** Features 0001 (generators), 0002 (ingestion), 0004 (RAG), 0007/0008 (API, frontend), ADR-0004, ADR-0008

## 1. Problem Statement

A presales engineer at *Andes Digital Networks* receives an RFP with a list of technical requirements and must answer, for each one: *does our product documentation support this, and where is the evidence?* Today this is manual reading across many technical manuals.

The platform already holds both sides: RFP requirements (ingested) and product manuals (ingested and indexed). This feature compares them and produces a **compliance report**: one row per RFP requirement with a verdict, a rationale and the manual passages that back it.

It produces **evidence for a human decision**, not a certification. Every verdict links to its sources, and uncertain cases are flagged for review.

## 2. Scope

### In scope
- Extend the synthetic manuals with a *Capabilities* section drawn from a fixed capability catalog (ADR-0008), so supported and unsupported requirements both exist and the right answer is known.
- Requirement extraction from an ingested RFP (deterministic parser).
- A compliance engine in `knowledge_assistant`: retrieval restricted to technical manuals, then a verdict.
- API: list RFPs, run a compliance check.
- Frontend: a fifth page, *Compliance*.
- An evaluation command that scores the engine against the known ground truth, with a baseline.

### Out of scope
- Real legal/contractual compliance, certification claims, multi-language documents.
- Requirements from Excel matrices (RFP PDFs only for now).
- Background jobs (a check runs synchronously, about 5 requirements per RFP).

## 3. Requirements

### Functional
| ID | Requirement |
|----|-------------|
| FR1 | `TechnicalManualGenerator` adds a *Capabilities* section whose statements come only from the supported subset of the capability catalog (ADR-0008). Generation stays reproducible per seed. |
| FR2 | `parse_requirements(text)` extracts the numbered items under *Technical Requirements* from an ingested RFP; pure function. |
| FR3 | Retrieval for a requirement is restricted to chunks of `technical_manual` documents. |
| FR4 | Four verdicts: `SUPPORTED`, `PARTIAL`, `NOT_EVIDENCED`, `NEEDS_REVIEW`. |
| FR5 | If no manual chunk clears the similarity threshold, the verdict is `NOT_EVIDENCED` **without calling the LLM** (same groundedness-first principle as Feature 0004). |
| FR6 | Otherwise an LLM judge returns a strict JSON verdict + rationale. Unparseable output becomes `NEEDS_REVIEW`, never a guessed verdict. |
| FR7 | Each row carries its evidence: manual file name, passage, similarity score. |
| FR8 | `GET /compliance/rfps` and `POST /compliance/check` (by RFP checksum), authenticated like every other route. |
| FR9 | Compliance page: pick an RFP, run the check, see a summary and a per-requirement table with expandable evidence. |
| FR10 | `compliance evaluate` CLI: scores verdicts against ground truth for both modes (retrieval-only vs retrieval + LLM judge) and a baseline. |

### Non-functional
| ID | Requirement |
|----|-------------|
| NFR1 | The engine depends on abstractions (`EmbeddingModel`, `VectorStoreRepository`, `LLMBackend`) and is fully unit-testable with the existing fakes. |
| NFR2 | No new infrastructure and no new uv project: this is part of the knowledge-assistant bounded context (ADR-0003). |
| NFR3 | Backward compatible: existing endpoints and indexed data keep working. |
| NFR4 | The evaluation reports honestly, including when the LLM judge does not beat retrieval-only. |

## 4. Architecture

```
RFP (ingested text) --parse_requirements--> [requirement, ...]
                                              |
   for each requirement:  embed -> similarity_search(type = technical_manual)
                                              |
                       no chunk >= threshold ?--yes--> NOT_EVIDENCED   (no LLM call)
                                              |no
                                  LLM judge (strict JSON) --> SUPPORTED | PARTIAL
                                              |                or NEEDS_REVIEW if unparseable
                                              v
                                   ComplianceReport (rows + evidence)
```

Placement: `knowledge_assistant/compliance.py` (engine, parser, models), `routers/compliance.py` in the API, `views/compliance.py` in the frontend.

## 5. Design Decisions

1. **Same retrieval stack, filtered by document type.** The vector store gains an optional `document_type` filter. `document_chunks` stays unchanged: the filter joins to `ingested_content` on the checksum (no migration, no re-embedding). Alternative considered: a `document_type` column on chunks, which is faster but needs a migration and re-index.
2. **Groundedness before the LLM.** No evidence above the threshold means `NOT_EVIDENCED` with zero LLM calls: cheaper, and the model cannot invent support.
3. **Strict JSON from the judge, defensive parsing.** A local 8B model will sometimes return malformed output. That becomes `NEEDS_REVIEW`, never a silently guessed verdict.
4. **A known answer key (ADR-0008).** The manuals support a fixed subset of the capability catalog. Because the RFP requirements are drawn from the full catalog, we know which requirements *should* be supported and can measure the engine instead of eyeballing it. Same philosophy as ADR-0004.
5. **Two modes, measured.** Retrieval-only vs retrieval + LLM judge. The extra LLM cost has to earn its place with a measured gain.
6. **Not a new uv project.** It reuses embeddings, vector store and LLM backend from `knowledge_assistant`; a separate project would duplicate or force a new shared package for no isolation benefit.

## 6. Trade-offs and Known Limitations

- **Synthetic wording overlaps by construction.** Manual statements and RFP requirements are drawn from the same phrase bank (manuals use varied templates, RFPs use "shall provide ..."). Retrieval will therefore look easier than on real documents. Results are reported as *on synthetic data*, not as a claim about real RFPs.
- **15 % label noise** from ADR-0004 also affects RFP requirements: a requirement can contain a phrase from a different category. The answer key is computed from the requirement's *actual phrase*, not its nominal category.
- **Product-level, not per-product.** Any manual can provide evidence; the catalog is company-wide. A real system would scope by the product being proposed.
- **Small LLM judge.** llama3 8B may mislabel `PARTIAL` cases. Reported as measured, not assumed.

## 7. Testing Strategy
- `parse_requirements`: well-formed RFP, missing section, multi-line items, stray numbering.
- Engine with fakes: no-evidence path never calls the LLM; judge JSON parsed; malformed JSON becomes `NEEDS_REVIEW`; evidence attached; type filter respected.
- Vector store: `document_type` filter on the in-memory double (and a SQL-level check against Postgres in the manual validation).
- Generator: manual contains only supported-catalog phrases; reproducible per seed.
- API: authentication, shape, unknown checksum returns 404.
- Frontend: page smoke test with a fake client.
- Evaluation on the regenerated corpus: accuracy, supported-class precision/recall, per mode, vs baseline (always `SUPPORTED`).
- Manual end-to-end against live Postgres + Ollama.

## 8. Data Migration
Technical manuals are regenerated (new content), re-ingested and re-indexed. Existing manual rows are removed first, as done for RFPs in Feature 0004. All data is synthetic and disposable.

## 9. Definition of Done
Implementation, tests, documentation (this doc + implementation notes), ADR-0008, example dataset (regenerated manuals), CI green, release notes v0.9.0 (bundled with Feature 0010 and the closure work).


---

# Implementation Notes (Feature 0009)

**Status:** Implemented and validated against the live stack (2026-10-24).
**Release:** v0.9.0 (bundled with Feature 0010).

## What was built

- **Ground truth (ADR-0008).** `shared_core.capabilities` defines the product capability catalog: 16 supported phrases (2 per category). Technical manuals now carry a "Capabilities" section drawn from it, seeded and reproducible. RFP requirements were already generated from a larger vocabulary, so some are supported and some are not, and we know which.
- **Engine.** `knowledge_assistant.compliance`: parse requirements, retrieve evidence from technical manuals only, then judge. Groundedness first: no passage above the similarity threshold gives `NOT_EVIDENCED` without calling the LLM. Judge output is strict JSON; anything unparseable gives `NEEDS_REVIEW`.
- **Retrieval filter.** `similarity_search(..., document_type=...)` joins `ingested_content` on the checksum. No schema migration.
- **Interfaces.** CLI (`compliance-check`, `compliance-evaluate`), API (`GET /compliance/rfps`, `POST /compliance/check`), and a Compliance page in the Streamlit frontend (v0.2.0).
- **Evaluation.** `compliance_eval`: baseline, threshold sweep (retrieval only), and judge on a sample.

## Measured results

Dataset: 100 RFPs, 110 technical manuals, synthetic. Labels come from the capability catalog.

| Strategy | Accuracy | F1 |
|---|---|---|
| Baseline "always SUPPORTED" | 0.540 | 0.701 |
| Retrieval only, threshold 0.30 (full set) | 0.728 | 0.799 |
| Retrieval only, threshold 0.30 (sample of 200) | 0.755 | 0.821 |
| Retrieval + LLM judge (sample of 200, temperature 0) | 0.890 | 0.911 |

Judge verdicts on the sample: 120 SUPPORTED, 14 PARTIAL, 64 NOT_EVIDENCED, 2 NEEDS_REVIEW. PARTIAL counts as "evidence found".

Threshold sweep: recall is 1.000 at 0.30 and 0.885 at 0.35, then drops quickly. The best F1 is at 0.30.

**Reading the numbers.**
- The limiting factor of retrieval alone is **precision (0.665)**, not recall. Unsupported requirements share category vocabulary with supported ones, so the manuals "talk about the topic" without guaranteeing the capability. The judge is what separates the two, and adds about 13 accuracy points over retrieval alone on the same sample.
- The expected risk that 200-word chunks would dilute the short Capabilities section did **not** materialize (recall 1.000 at 0.30).
- Sample of 200 gives a sampling margin of roughly +-4 points.
- **These numbers are optimistic**: synthetic data with shared vocabulary, and the threshold was selected on the same data it is evaluated on (no held-out set).

## Findings and bugs

1. **Stale duplicate RFP rows.** `document_metadata` held 110 RFP rows for 100 file paths. Regenerating the RFPs (ADR-0004) changed their content and checksums, and ingestion deduplicates by checksum, not by path, so the old rows stayed. It was detected because `compliance-check --rfp rfp_0003.pdf` correctly refused to guess between two matches. Cleanup: delete the older row per path from `ingested_content` and `document_metadata`, truncate `document_chunks`, reindex. Follow-up: make regeneration or ingestion path-aware.
2. **The judge was non-deterministic.** The Ollama call did not set a temperature, so the same requirement gave PARTIAL in the CLI and NOT_EVIDENCED in the UI. Fix: the compliance judge now runs with `temperature=0` and a fixed seed (`/ask` is unchanged). Verified: two runs over the same RFP are identical, and NEEDS_REVIEW fell from 10 to 2 of 200. Earlier measurements (0.92, 0.82, 0.895) were single draws from a stochastic judge and were discarded in favor of the table above.
3. **Evidence preview hid the proof.** The UI cut each passage to 300 characters, which showed the start of the chunk instead of the sentence the judge cited. Now the full passage is shown.
4. **FastAPI dependency gotcha, again.** The RFP source dependency returns a factory that the endpoint calls, so a request with a missing header (422) never touches the database. Covered by a test.
5. **Persistent judge error.** "Standardized data exchange formats" is not in the catalog, but the judge marks it PARTIAL with a vague rationale (`rfp_0003`, requirement 5). Without the judge, retrieval alone marks it SUPPORTED, so the judge reduces the error but does not remove it.

## Deviations from the design

- The document-type filter is implemented as a join, not a new column, to avoid a migration.
- Judge temperature fixed at 0 (not in the original design).

## Known limitations

- Single 8B local model as judge; no held-out threshold selection; synthetic data only.
- The tool supports a human decision. It is not a compliance certification, and the page says so.
- Judge runs are synchronous: a full RFP takes seconds per requirement.

## Future work

- Require that the judge's quoted sentence appears verbatim in the cited passage (reject otherwise).
- Try a larger local model for the judge and compare on the same sample.
- Hold out part of the requirements to select the threshold.
- Path-aware ingestion to avoid stale rows.
