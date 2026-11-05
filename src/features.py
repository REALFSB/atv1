"""Compatibility exports for feature engineering."""

from .ml.features import (
    CATEGORICAL,
    FEATURE_COLUMNS,
    NUMERIC,
    OVERTIME_HIGH_THRESHOLD,
    add_features,
    build_preprocessor,
    feature_matrix,
)

__all__ = [
    "CATEGORICAL",
    "FEATURE_COLUMNS",
    "NUMERIC",
    "OVERTIME_HIGH_THRESHOLD",
    "add_features",
    "build_preprocessor",
    "feature_matrix",
]
