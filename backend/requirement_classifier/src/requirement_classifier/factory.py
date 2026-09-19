"""Classifier factory (FR8/NFR3): same extensibility pattern used
throughout this codebase (generators in Feature 0001, parsers in
Feature 0002).

Feature 0006 adds "neural_network" here -- the exact scenario this
factory was built for: a new model registered without touching the
training/evaluation pipeline at all.
"""
from sklearn.base import ClassifierMixin
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

_REGISTRY: dict[str, type[ClassifierMixin]] = {
    "logistic_regression": LogisticRegression,
    "neural_network": MLPClassifier,
}

_DEFAULT_PARAMS: dict[str, dict] = {
    "logistic_regression": {"max_iter": 1000},
    # Feature 0006: a single hidden layer is a reasonable starting point
    # for ~200 examples -- a much larger/deeper network would be more
    # likely to overfit than to genuinely learn more at this data scale.
    "neural_network": {"hidden_layer_sizes": (50,), "max_iter": 1000},
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
