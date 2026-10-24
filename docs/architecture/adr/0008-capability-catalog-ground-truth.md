# ADR-0008: Capability catalog as ground truth for compliance evaluation

## Status
Proposed

## Context
Feature 0009 asks whether a technical manual supports an RFP requirement. To know whether the engine is *right*, we need to know the right answer. Today the manuals contain generic Faker text with no capability statements, so every requirement would be unsupported and nothing could be measured. If instead every manual contained every capability, every requirement would be supported. In both cases the evaluation says nothing.

## Decision
Define a **capability catalog**: the existing category phrase bank from ADR-0004 (`_CATEGORY_VOCAB`, 4 phrases per category). A fixed, documented subset of it (2 phrases per category, chosen deterministically) is the **supported set**: what the fictional company's products actually provide.

- `TechnicalManualGenerator` gets a *Capabilities* section whose statements are drawn **only from the supported set**, rendered through several manual-style templates (for example "The product delivers ...", "Built-in support for ...") so wording differs from the RFP's "The solution shall provide ...".
- RFP requirements keep drawing from the **full** catalog (including the ADR-0004 noise). About half of the requirements are therefore unsupported by construction.
- **Ground truth** for a requirement = whether its actual phrase belongs to the supported set. It is derived from the requirement text, so it stays correct under label noise.

## Alternatives considered
- **Random coverage per manual (for example 70 %).** With ~110 manuals, almost every phrase appears somewhere, so nearly everything is supported and the evaluation is uninformative.
- **Hand-labeled evaluation set.** Realistic, but small and costly to build; the synthetic answer key scales with the corpus and stays reproducible.
- **LLM-as-judge for the ground truth.** Circular: it would grade the engine with the same kind of model it uses.

## Consequences
- Technical manuals must be regenerated and re-ingested/re-indexed (disposable synthetic data).
- The evaluation measures the engine on data with controlled vocabulary overlap, so absolute scores are optimistic compared with real documents. This is stated wherever results are reported.
- The supported set is a documented constant: changing it changes the answer key, and evaluation results are only comparable across runs with the same set.

## References
- ADR-0004: Correlated synthetic labels.
- Feature 0009: Compliance Validation.
