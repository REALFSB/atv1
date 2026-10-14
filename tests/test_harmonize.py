import pandas as pd
import pytest

from src.harmonize import UNIFIED_COLUMNS, _pct_to_1_5, build_unified, clean, quality_report


def test_pct_to_1_5_scale():
    assert _pct_to_1_5(pd.Series([0, 50, 100, 150])).tolist() == [1, 3, 5, 5]


def test_build_unified_stacks_sources_and_drops_pii(tmp_path):
    pd.DataFrame({"Name": ["Fulano Silva"], "Age": [30], "Gender": ["M"], "Projects Completed": [5],
                  "Productivity (%)": [80], "Satisfaction Rate (%)": [50], "Feedback Score": [4.0],
                  "Department": ["IT"], "Position": ["Analyst"], "Joining Date": ["Jan-20"],
                  "Salary": [60000]}).to_csv(tmp_path / "hr_dashboard_data.csv", index=False)
    df = build_unified(str(tmp_path))
    assert list(df.columns) == UNIFIED_COLUMNS
    assert "Fulano" not in df.to_string() and df.loc[0, "department"] == "IT"  # sigla preservada
    assert df.loc[0, "monthly_salary"] == 5000 and df.loc[0, "satisfaction"] == 3
    assert not df.loc[0, "has_label"]


def test_clean_removes_duplicates_and_out_of_range():
    base = {c: [None, None, None] for c in UNIFIED_COLUMNS}
    base.update({"employee_id": ["A", "A", "B"], "source": ["x"] * 3, "department": [" IT "] * 3,
                 "job_title": ["a"] * 3, "education_level": ["b"] * 3, "age": [30, 30, 200]})
    out = clean(pd.DataFrame(base))
    assert len(out) == 2 and out["department"].iloc[0] == "IT" and pd.isna(out.loc[1, "age"])


def test_build_unified_requires_some_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_unified(str(tmp_path))
    assert quality_report(pd.DataFrame({"source": ["a"], "has_label": [True]}))["com_rotulo"] == 1
