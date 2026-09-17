"""Classifier factory (FR8/NFR3): same extensibility pattern used
throughout this codebase (generators in Feature 0001, parsers in
Feature 0002).

To add a new classifier (Decision Tree, Random Forest, SVM -- following
the roadmap's Hands-On ML chapter progression): add one entry here.
No other file needs to change.
"""
from sklearn.base import ClassifierMixin
from sklearn.linear_model import LogisticRegression

_REGISTRY: dict[str, type[ClassifierMixin]] = {
    "logistic_regression": LogisticRegression,
}

_DEFAULT_PARAMS: dict[str, dict] = {
    "logistic_regression": {"max_iter": 1000},
}


class ClassifierFactory:
    def create(self, model_type: str, seed: int) -> ClassifierMixin:
        try:
            classifier_cls = _REGISTRY[model_type]
        except KeyError as exc:
            raise ValueError(f"No classifier registered for: {model_type}") from exc

        params = dict(_DEFAULT_PARAMS.get(model_type, {}))
        params["random_state"] = seed
        return classifier_cls(**params)
