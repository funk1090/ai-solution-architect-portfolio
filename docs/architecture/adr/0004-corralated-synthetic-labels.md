# ADR-0004: Correlated synthetic labels for ML trainability

## Status
Accepted

## Context
Phase 3 (Requirement Intelligence Engine) requires training a classifier
to predict a requirement's Category and Priority from its Description
text. The original synthetic data generator (Feature 0001,
`EnterpriseFakerProvider`) assigned Category and Priority independently
at random, with no relationship to the generated Description text. A
classifier trained on this data would only be able to match the
baseline accuracy of predicting the most frequent class — not because
of a modeling failure, but because the data contains no learnable
signal between input (text) and target (label).

This was caught before any model training was attempted, by questioning
whether the target variable was predictable at all — not after seeing
poor model performance and assuming the model or features were at fault.

## Decision
`EnterpriseFakerProvider` gains a new method, `correlated_requirement()`,
used only by `ExcelRequirementsGenerator`, which:

1. Selects Category and Priority first (as before).
2. Builds the Description using a **category-specific vocabulary bank**
   (e.g., Security → "end-to-end encryption", "multi-factor
   authentication"; Performance → "sub-second response times",
   "high-throughput processing") and a **priority-specific phrasing
   bank** (e.g., Critical → "must be delivered immediately"; Low →
   "would be a nice-to-have enhancement").
3. Injects **controlled noise**: 15% of the time, the vocabulary is
   drawn from a random category/priority instead of the correct one.

The existing `technical_requirement()` method (used by `RFPGenerator`
and `TechnicalManualGenerator`, which have no Category/Priority to
correlate against) is left unchanged.

## Alternatives considered

**Leave labels random, document as a pipeline-mechanics demo**
- Advantages: zero changes to already-released Feature 0001 code; fully
  honest about the limitation.
- Disadvantages: a near-baseline accuracy result is a weak portfolio
  artifact and invites the (incorrect) assumption that the ML
  implementation itself is flawed, rather than the data.

**Fully deterministic correlation (no noise)**
- Advantages: simplest to implement; guarantees very high accuracy.
- Disadvantages: a trivial keyword-lookup problem is not a meaningful
  demonstration of a classifier — 99-100% accuracy on an artificially
  easy problem reads as suspicious rather than impressive to anyone
  reviewing the work critically.

**Correlated Category, random Priority** (the initially proposed
middle ground)
- Advantages: reflects a real-world argument that priority depends on
  business context, not just requirement wording.
- Disadvantages: unnecessarily narrows Phase 3's scope when the fully
  correlated approach (with noise) is not meaningfully harder to build
  and produces a more complete demonstration (multi-label
  classification, not single-label).

## Consequences
- Feature 0001's `EnterpriseFakerProvider` and `ExcelRequirementsGenerator`
  must be updated and the existing v0.1.0 dataset regenerated —
  acceptable since all data is synthetic and disposable.
- Phase 3's classifier has a genuinely learnable but non-trivial
  problem: a well-tuned model should meaningfully outperform the
  majority-class baseline, but is not expected to reach 100% accuracy
  (the 15% noise rate caps realistic ceiling accuracy).
- This noise rate (15%) becomes a documented, tunable parameter —
  future phases could increase or decrease it to make the classification
  problem harder or easier without redesigning the generator.

## References
- Feature 0001: Synthetic Enterprise Document Generator.
- Feature 0003 (Phase 3, forthcoming): Requirement Intelligence Engine.
