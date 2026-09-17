# ADR-0005: ML model evaluation and persistence strategy

## Status
Accepted

## Context
Feature 0003 introduces the platform's first machine learning model. Two
decisions needed to be made explicitly rather than defaulted into: how
the model's performance is measured given a small dataset, and how the
trained artifact is stored and tracked over time.

## Decision

**Evaluation**: stratified k-fold cross-validation (5 folds) is used
instead of a single train/test split, with every reported metric
(accuracy, precision, recall, F1) accompanied by its standard deviation
across folds. A `DummyClassifier` (most-frequent-class strategy) is
evaluated the same way and reported alongside the real model's results
in every run, not as a separate one-off check.

**Persistence**: the final model (fit on the complete dataset after
cross-validation has validated its performance) is saved as a single
`joblib` file. A companion JSON file records the run's configuration
(model type, hyperparameters, seed) and its cross-validated metrics.
No model registry or experiment-tracking platform (e.g., MLflow) is
introduced at this stage.

## Alternatives considered

**Single train/test split**
- Advantages: simpler to implement and explain; matches how many
  introductory ML tutorials present evaluation.
- Disadvantages: with ~200 examples across 8 classes, a single 80/20
  split leaves very few test examples per class, making the resulting
  metric highly sensitive to which examples happened to land in the
  test set — not a reliable signal at this data scale.

**MLflow or a similar model registry**
- Advantages: proper experiment tracking, artifact versioning, and a
  UI for comparing runs — the right tool once experiment volume grows.
- Disadvantages: at one developer and a handful of training runs, this
  is infrastructure solving a problem that doesn't exist yet. Standing
  up and maintaining a tracking server would be over-engineering
  relative to the project's current scale, contradicting the
  "avoid overengineering" principle this project holds itself to.

## Consequences
- Every training run's metrics are directly comparable to the baseline
  by construction, not by remembering to check separately — this
  directly operationalizes the lesson from ADR-0004 (don't trust a
  model's number without knowing what "doing nothing" would score).
- Multiple training runs will produce multiple joblib/JSON pairs on
  disk; without a registry, comparing many runs at once will become
  manually tedious. This is an accepted, documented limitation — see
  Future Improvements in Feature 0003 for the trigger condition
  (experiment volume) that would justify revisiting this with MLflow.
- The 5-fold choice is a reasonable default for a dataset this size,
  not scientifically tuned; it should be revisited if the dataset grows
  substantially larger in a later phase.

## References
- Feature 0003: Requirement Intelligence Engine.
- ADR-0004: Correlated synthetic labels for ML trainability.
- Hands-On Machine Learning with Scikit-Learn, Keras & TensorFlow
  (Géron) — Ch. 2, End-to-End Machine Learning Project (cross-validation
  guidance).
