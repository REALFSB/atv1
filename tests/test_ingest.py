import numpy as np
import pandas as pd
import pytest

from src.ingest import (REQUIRED_COLUMNS, CsvSource, DataQualityError, DataSource,
                        KaggleHRSource, SyntheticSource, load_operations, pseudonymize, validate)


def test_synthetic_has_required_schema():
    df = SyntheticSource(n_employees=50).load()
    assert list(df.columns) == REQUIRED_COLUMNS and len(df) == 50


def test_validate_rejects_missing_column():
    df = SyntheticSource(20).load().drop(columns=["department"])
    with pytest.raises(DataQualityError, match="department"):
        validate(df)


def test_validate_rejects_more_than_5pct_nulls_and_names_column():  # US3
    df = SyntheticSource(100).load()
    df.loc[df.index[:20], "overtime_hours"] = np.nan  # 20% nulos
    with pytest.raises(DataQualityError, match="overtime_hours"):
        validate(df)


def test_pseudonymize_is_deterministic_and_hides_ids():  # US4
    df = SyntheticSource(20).load()
    a, b = pseudonymize(df, "s"), pseudonymize(df, "s")
    assert a["employee_id"].equals(b["employee_id"])
    assert not set(a["employee_id"]) & set(df["employee_id"])
    assert not a["employee_id"].equals(pseudonymize(df, "outro")["employee_id"])


def test_sensitive_and_leak_columns_are_dropped():  # US4 + vazamento
    class Sensitive(DataSource):
        def load(self):
            df = SyntheticSource(30).load()
            df["health_condition"], df["sick_days"], df["age"], df["gender"] = "x", 9, 40, "F"
            return df
    out = load_operations(Sensitive())
    assert not {"health_condition", "sick_days", "age", "gender"} & set(out.columns)


def test_csv_source_applies_column_map(tmp_path):
    p = tmp_path / "d.csv"
    SyntheticSource(10).load().rename(columns={"department": "setor"}).to_csv(p, index=False)
    assert "department" in CsvSource(str(p), {"setor": "department"}).load().columns


# ---- bases reais: usa os CSVs se existirem em data/raw ----
RAW = "data/raw"


@pytest.mark.skipif(not __import__("os").path.exists(f"{RAW}/hr_dashboard_data.csv"), reason="bases do Kaggle ausentes")
def test_kaggle_source_loads_labeled_rows_without_pii():
    df = load_operations(KaggleHRSource(RAW))
    assert len(df) == 100_000 and set(df["absent"]) == {0, 1}
    assert not {"name", "age", "sick_days", "gender"} & set(df.columns)
