"""Testes do módulo dashboard: agregados corretos, LGPD e arquivo lido pelo painel."""
import json

import numpy as np
import pandas as pd
import pytest

from src import dashboard as dash
from src.harmonize import FILES


@pytest.fixture()
def raw_dir(tmp_path):
    """Três CSVs mínimos, no formato original das bases do Kaggle."""
    ext = pd.DataFrame({
        "Employee_ID": range(1, 13), "Department": ["IT"] * 6 + ["HR"] * 6, "Gender": "F", "Age": 30,
        "Job_Title": "Analyst", "Hire_Date": "2020-01-01 08:00:00", "Years_At_Company": 4,
        "Education_Level": "Bachelor", "Performance_Score": [1, 3, 5, 5, 3, 1] * 2, "Monthly_Salary": 5000,
        "Work_Hours_Per_Week": 40, "Projects_Handled": 10, "Overtime_Hours": 10,
        "Sick_Days": [0, 5, 11, 14, 2, 12] * 2, "Remote_Work_Frequency": 50, "Team_Size": 8,
        "Training_Hours": 20, "Promotions": 0, "Employee_Satisfaction_Score": 3.0,
        "Resigned": [True] + [False] * 11})
    ext.to_csv(tmp_path / FILES["extended"], index=False)
    pd.DataFrame({"Name": ["A", "B"], "Age": [30, 40], "Gender": "M", "Projects Completed": [5, 6],
                  "Productivity (%)": [50, 100], "Satisfaction Rate (%)": [50, 50], "Feedback Score": 4.0,
                  "Department": "IT", "Position": "Analyst", "Joining Date": ["Jan-20", "Feb-21"],
                  "Salary": [60000, 72000]}).to_csv(tmp_path / FILES["hr_dashboard"], index=False)
    pd.DataFrame({"Employee_ID": ["E1"], "Department": ["Data Science"], "Experience_Years": [3],
                  "Technical_Skill_Score": 90, "Communication_Score": 80, "Training_Hours": 100,
                  "Projects_Completed": 10, "Avg_Weekly_Work_Hours": 42, "Productivity_Score": [80],
                  "Salary_USD": 80000}).to_csv(tmp_path / FILES["productivity"], index=False)
    return str(tmp_path)


def test_productivity_index_is_inverse_of_harmonize_scale():
    df = pd.DataFrame({"performance_score": [1, 3, 5]})
    assert dash.with_productivity_index(df)["productivity_index"].tolist() == [0, 50, 100]


def test_aggregates_keep_sum_and_count(raw_dir):
    data = dash.build_dashboard_data(raw_dir)
    ext_it = next(r for r in data["by_dept"] if r["source"] == "extended" and r["department"] == "IT")
    assert ext_it["n"] == 6
    soma, n = ext_it["prod"]
    assert n == 6 and soma / n == pytest.approx((0 + 50 + 100 + 100 + 50 + 0) / 6)
    assert ext_it["sick_high"] == 3  # 11, 14 e 12 dias
    assert ext_it["resigned"] == 1


def test_pooling_sources_is_weighted_mean(raw_dir):
    data = dash.build_dashboard_data(raw_dir)
    it = [r for r in data["by_dept"] if r["department"] == "IT"]
    soma = sum(r["prod"][0] for r in it); n = sum(r["prod"][1] for r in it)
    assert n == 8 and soma / n == pytest.approx((300 + 50 + 100) / 8)  # (6 linhas: soma 300) + 2 do HR Dashboard


def test_small_groups_hide_absence_data(raw_dir):
    data = dash.build_dashboard_data(raw_dir)
    for r in data["by_dept"]:
        if r["n"] < dash.MIN_GROUP:
            assert r["sick"] == [0.0, 0] and r["sick_high"] == 0


def test_export_is_valid_js_and_has_no_nan(raw_dir, tmp_path):
    data = dash.build_dashboard_data(raw_dir)
    out = dash.export_dashboard_js(data, str(tmp_path / "dashboard-data.js"))
    text = open(out, encoding="utf-8").read()
    assert text.startswith("window.DASH_DATA = ") and "NaN" not in text
    payload = json.loads(text[len("window.DASH_DATA = "):].rstrip(";\n"))
    assert set(payload) >= {"params", "sources", "quality", "by_dept", "by_year"}
    assert {m["id"] for m in payload["params"]["metas"]} == {"prod", "sat", "ot", "sick"}


def test_no_personal_names_in_output(raw_dir):
    text = json.dumps(dash.build_dashboard_data(raw_dir), ensure_ascii=False)
    assert '"Name"' not in text and '"A"' not in text and "Gender" not in text
