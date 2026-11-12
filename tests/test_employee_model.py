"""Testes da ingestão de funcionários, do modelo por funcionário e do gerador do painel.
Usam bases sintéticas pequenas no esquema do Kaggle, para não depender do CSV de 11 MB."""
import json

import numpy as np
import pandas as pd
import pytest

from src.dashboard import build, write_js
from src.data.employees import SICK_HIGH_DAYS, load_employees, normalize_employees
from src.ml.kaggle_risk import (
    FEATURES,
    export_js,
    main,
    precision_at_top,
    score_employees,
    train_employee_model,
)

DEPTS = ["IT", "HR", "Sales", "Finance"]
JOBS = ["Analyst", "Manager", "Engineer"]


def kaggle_like(n: int = 800, signal: bool = True, seed: int = 0) -> pd.DataFrame:
    """Base no esquema do Kaggle. Com `signal`, Sick_Days cresce com horas extras."""
    rng = np.random.default_rng(seed)
    years = rng.integers(0, 10, n)
    hire = pd.Timestamp("2024-09-04 08:03:05") - pd.to_timedelta(years * 365 + 30, unit="D")
    overtime = rng.integers(0, 30, n)
    noise = rng.integers(0, 15, n)
    sick = np.clip(overtime // 2 + rng.integers(-2, 3, n), 0, 14) if signal else noise
    return pd.DataFrame({
        "Employee_ID": np.arange(1, n + 1), "Department": rng.choice(DEPTS, n),
        "Gender": rng.choice(["Male", "Female"], n), "Age": years + rng.integers(20, 40, n),
        "Job_Title": rng.choice(JOBS, n), "Hire_Date": hire.astype(str),
        "Years_At_Company": years, "Education_Level": rng.choice(["Bachelor", "Master"], n),
        "Performance_Score": rng.integers(1, 6, n),
        "Monthly_Salary": rng.integers(4, 9, n) * 1000.0,
        "Work_Hours_Per_Week": rng.integers(30, 60, n), "Projects_Handled": rng.integers(0, 50, n),
        "Overtime_Hours": overtime, "Sick_Days": sick,
        "Remote_Work_Frequency": rng.choice([0, 50, 100], n),
        "Team_Size": rng.integers(1, 20, n), "Training_Hours": rng.integers(0, 100, n),
        "Promotions": rng.integers(0, 3, n),
        "Employee_Satisfaction_Score": rng.uniform(1, 5, n).round(2),
        "Resigned": rng.choice([True, False], n, p=[.1, .9]),
    })


# ---------------------------------------------------------------- ingestão
def test_normalize_drops_gender_and_derives_columns():
    df = normalize_employees(kaggle_like(50))
    assert "Gender" not in df.columns and "gender" not in df.columns
    derived = {"tenure_months", "overtime_ratio", "productivity_index", "sick_high", "qc06_ok"}
    assert derived <= set(df)
    assert df["productivity_index"].between(0, 100).all()


@pytest.mark.parametrize(("sick", "high"), [(SICK_HIGH_DAYS - 1, 0), (SICK_HIGH_DAYS, 1), (14, 1)])
def test_sick_high_threshold(sick, high):
    raw = kaggle_like(1)
    raw.loc[0, "Sick_Days"] = sick
    assert normalize_employees(raw).loc[0, "sick_high"] == high


def test_qc06_violations_are_flagged_for_quarantine():
    raw = kaggle_like(3)
    raw.loc[1, ["Age", "Years_At_Company"]] = [22, 9]   # admitido aos 13
    flags = normalize_employees(raw)["qc06_ok"].tolist()
    assert flags == [True, False, True]


def test_load_employees_pseudonymizes_ids(tmp_path):
    p = tmp_path / "k.csv"
    kaggle_like(5).to_csv(p, index=False)
    ids = load_employees(str(p), salt="s")["employee_id"]
    assert ids.str.fullmatch(r"[0-9a-f]{12}").all() and "1" not in ids.tolist()


def test_missing_column_is_reported():
    with pytest.raises(KeyError, match="Sick_Days"):
        normalize_employees(kaggle_like(5).drop(columns=["Sick_Days"]))


# ---------------------------------------------------------------- modelo
def test_model_learns_when_target_has_signal():
    m = train_employee_model(normalize_employees(kaggle_like(1200, signal=True))).metrics
    assert m["roc_auc"] > 0.85 and m["meets_targets"]


def test_model_is_near_chance_when_target_is_noise():
    """Protege contra conclusões erradas: sem sinal, AUC fica perto de 0,5."""
    m = train_employee_model(normalize_employees(kaggle_like(1200, signal=False))).metrics
    assert 0.35 < m["roc_auc"] < 0.65 and not m["meets_targets"]


def test_quarantined_rows_are_excluded_from_training_and_ranking():
    raw = kaggle_like(400)
    raw.loc[:9, ["Age", "Years_At_Company"]] = [22, 9]
    df = normalize_employees(raw)
    result = train_employee_model(df)
    assert result.metrics["quarantined_qc06"] == 10
    assert result.metrics["n_train"] + result.metrics["n_test"] == 390
    assert len(score_employees(df, result.pipeline)) == 390


def test_ranking_is_sorted_with_bands_and_factors():
    df = normalize_employees(kaggle_like(400))
    ranked = score_employees(df, train_employee_model(df).pipeline)
    assert ranked["risk"].is_monotonic_decreasing
    assert set(ranked["band"]) <= {"Alta", "Média", "Baixa"}
    assert ranked["factors"].str.count(",").eq(2).all()
    assert ranked["rank"].tolist() == list(range(1, len(ranked) + 1))


def test_model_does_not_use_protected_attributes():
    assert not {"age", "gender"} & set(FEATURES)


@pytest.mark.parametrize(("y", "p", "expected"), [
    ([1, 0, 0, 0, 0, 0, 0, 0, 0, 0], [.9, .1, .1, .1, .1, .1, .1, .1, .1, .1], 1.0),
    ([0, 1, 0, 0, 0, 0, 0, 0, 0, 0], [.9, .1, .1, .1, .1, .1, .1, .1, .1, .1], 0.0),
])
def test_precision_at_top(y, p, expected):
    assert precision_at_top(np.array(y), np.array(p), share=0.1) == expected


def test_export_js_labels_semi_synthetic_dataset(tmp_path):
    df = normalize_employees(kaggle_like(300))
    res = train_employee_model(df)
    path = export_js(score_employees(df, res.pipeline), res.metrics, str(tmp_path / "r.js"),
                     "base_2_otimizado.csv", top=20)
    txt = (tmp_path / "r.js").read_text(encoding="utf-8")
    payload = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
    assert path.endswith("r.js") and payload["source"] == "kaggle_semissintetico"
    assert "SEMI-SINTÉTICA" in payload["source_label"] and len(payload["ranking"]) == 20
    assert payload["total"] == 300


def test_cli_refuses_blocked_dataset(tmp_path):
    raw = kaggle_like(300)
    raw.loc[1, "Employee_ID"] = 1          # ID duplicado → QC02 (crítica) reprova
    csv = tmp_path / "k.csv"
    raw.to_csv(csv, index=False)
    args = ["--data", str(csv), "--out", str(tmp_path / "a"), "--web-out", str(tmp_path / "r.js")]
    assert main(args) == 1 and not (tmp_path / "r.js").exists()
    assert main([*args, "--skip-quality-gate"]) == 0


def test_cli_writes_model_metrics_and_panel(tmp_path):
    csv = tmp_path / "k.csv"
    kaggle_like(300).to_csv(csv, index=False)
    rc = main(["--data", str(csv), "--out", str(tmp_path / "a"), "--web-out",
               str(tmp_path / "r.js"), "--top", "5"])
    assert rc == 0
    assert json.loads((tmp_path / "a" / "metrics.json").read_text())["n_test"] == 75
    assert (tmp_path / "a" / "ranking.csv").exists() and (tmp_path / "r.js").exists()


# ---------------------------------------------------------------- gerador do painel
SNAP = {
    "params": {"limite_absenteismo_dias": 11}, "sources": {"hr": {"label": "HR", "linhas": 2}},
    "by_dept": [{"source": "hr", "department": "HR", "n": 2}], "by_year": [],
    "rows": 2, "labeled_rows": 0, "null_counts": {"sick_days": 2},
}


def test_dashboard_aggregates_extended_and_keeps_frozen_sources():
    raw = kaggle_like(100)
    data = build(raw, SNAP)
    ext = [r for r in data["by_dept"] if r["source"] == "extended"]
    assert sum(r["n"] for r in ext) == 100 and data["by_dept"][-1]["source"] == "hr"
    assert sum(r["sick"][0] for r in ext) == raw["Sick_Days"].sum()
    assert sum(r["sick_high"] for r in ext) == int((raw["Sick_Days"] >= 11).sum())
    assert sum(r["n"] for r in data["by_year"]) == 100
    assert data["quality"]["linhas"] == 102
    assert data["quality"]["nulos_pct"]["sick_days"] == round(2 / 102 * 100, 1)


def test_dashboard_js_is_valid(tmp_path):
    out = write_js(build(kaggle_like(20), SNAP), tmp_path / "d.js")
    txt = out.read_text(encoding="utf-8")
    assert txt.startswith("window.DASH_DATA = ") and json.loads(txt[19:-2])["sources"]["extended"]
