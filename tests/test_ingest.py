import numpy as np
import pandas as pd
import pytest

from src.ingest import (REQUIRED_COLUMNS, CsvSource, DataQualityError, DataSource,
                        SyntheticSource, load_operations, pseudonymize, validate)


def test_synthetic_has_required_schema():
    df = SyntheticSource(n_employees=10, n_days=5).load()
    assert list(df.columns) == REQUIRED_COLUMNS and len(df) == 50


def test_validate_rejects_missing_column():
    df = SyntheticSource(5, 5).load().drop(columns=["shift"])
    with pytest.raises(DataQualityError, match="shift"):
        validate(df)


def test_validate_rejects_more_than_5pct_nulls_and_names_column():  # US3
    df = SyntheticSource(10, 10).load()
    df.loc[df.index[:20], "distance_km"] = np.nan  # 20% nulos
    with pytest.raises(DataQualityError, match="distance_km"):
        validate(df)


def test_pseudonymize_is_deterministic_and_hides_ids():  # US4
    df = SyntheticSource(5, 3).load()
    a, b = pseudonymize(df, "s"), pseudonymize(df, "s")
    assert a["employee_id"].equals(b["employee_id"])
    assert not set(a["employee_id"]) & set(df["employee_id"])
    assert not a["employee_id"].equals(pseudonymize(df, "outro")["employee_id"])


def test_sensitive_columns_are_dropped():  # US4
    class Sensitive(DataSource):
        def load(self):
            df = SyntheticSource(5, 5).load()
            df["health_condition"] = "x"
            df["social_drinker"] = 1
            return df
    out = load_operations(Sensitive())
    assert "health_condition" not in out and "social_drinker" not in out


def test_csv_source_applies_column_map(tmp_path):
    p = tmp_path / "d.csv"
    SyntheticSource(5, 5).load().rename(columns={"sector": "setor"}).to_csv(p, index=False)
    df = CsvSource(str(p), {"setor": "sector"}).load()
    assert "sector" in df.columns
