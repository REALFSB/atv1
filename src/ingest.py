"""Compatibility exports for the data-ingestion package."""

from .data.ingest import (
    MAX_NULL_RATE,
    REQUIRED_COLUMNS,
    SENSITIVE_COLUMNS,
    CsvSource,
    DataQualityError,
    DataSource,
    SyntheticSource,
    load_operations,
    make_source,
    pseudonymize,
    validate,
)

__all__ = [
    "MAX_NULL_RATE",
    "REQUIRED_COLUMNS",
    "SENSITIVE_COLUMNS",
    "CsvSource",
    "DataQualityError",
    "DataSource",
    "SyntheticSource",
    "load_operations",
    "make_source",
    "pseudonymize",
    "validate",
]
