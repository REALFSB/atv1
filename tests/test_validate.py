"""Testes da validação de qualidade (US11): cada regra tem um caso que passa, casos de
borda e um defeito que só ela detecta. Ordem TDD proposta em docs/xp_implementation.md."""
import json

import pandas as pd
import pytest

from src.validate import (
    RULES,
    RULES_BY_ID,
    STATUS_EMPTY,
    STATUS_FAIL,
    STATUS_PASS,
    evaluate_rule,
    load_dataset,
    load_sql_queries,
    main,
    normalize,
    render_markdown,
    run_checks,
    run_sql_checks,
    sql_matches,
    summarize,
)

BASE_ROW = {
    "Employee_ID": "1", "Department": "IT", "Gender": "Female", "Age": "40",
    "Job_Title": "Analyst", "Hire_Date": "2019-09-04 08:03:05.556036",
    "Years_At_Company": "5", "Education_Level": "Master", "Performance_Score": "4",
    "Monthly_Salary": "6500.0", "Work_Hours_Per_Week": "40", "Projects_Handled": "10",
    "Overtime_Hours": "5", "Sick_Days": "3", "Remote_Work_Frequency": "50",
    "Team_Size": "8", "Training_Hours": "20", "Promotions": "1",
    "Employee_Satisfaction_Score": "3.5", "Resigned": "False",
}


def make_df(n: int = 10, **overrides_by_index) -> pd.DataFrame:
    """n registros válidos com IDs 1..n; overrides_by_index={'r3': {...}} altera a linha 3."""
    rows = []
    for i in range(n):
        row = dict(BASE_ROW, Employee_ID=str(i + 1))
        row.update(overrides_by_index.get(f"r{i}", {}))
        rows.append(row)
    return normalize(pd.DataFrame(rows))


def failed_rules(df: pd.DataFrame) -> dict[str, int]:
    return {r.id: r.failed for r in run_checks(df) if r.failed}


# ---------------------------------------------------------------- caminho feliz
def test_clean_data_passes_every_rule():
    results = run_checks(make_df())
    assert [r.status for r in results] == [STATUS_PASS] * 6
    assert summarize(results)["verdict"] == "LIBERADA"


def test_six_rules_cover_the_four_dimensions():
    assert len(RULES) == 6
    assert {r.dimension for r in RULES} == {"Completude", "Unicidade", "Validade", "Consistência"}


# ---------------------------------------------------------------- um defeito, uma regra
@pytest.mark.parametrize(
    ("override", "expected_rule"),
    [
        ({"Department": ""}, "QC01"),
        ({"Department": "   "}, "QC01"),              # só espaços conta como vazio
        ({"Monthly_Salary": "N/D"}, "QC01"),          # não numérico vira ausente
        ({"Resigned": ""}, "QC01"),
        ({"Gender": "M"}, "QC03"),
        ({"Education_Level": "Doutorado"}, "QC03"),
        ({"Resigned": "Sim"}, "QC03"),
        ({"Performance_Score": "7"}, "QC04"),
        ({"Employee_Satisfaction_Score": "0.5"}, "QC04"),
        ({"Work_Hours_Per_Week": "120"}, "QC04"),
        ({"Monthly_Salary": "-10"}, "QC04"),
        ({"Years_At_Company": "8"}, "QC05"),          # admissão em 2019 → 5 anos, não 8
        ({"Hire_Date": "2025-01-10", "Years_At_Company": "0"}, "QC05"),  # admissão no futuro
    ],
)
def test_single_defect_is_caught_only_by_its_rule(override, expected_rule):
    assert failed_rules(make_df(r4=override)) == {expected_rule: 1}


def test_admission_before_18_fails_qc06_only():
    # 22 anos com 5 anos de casa → admitido aos 17
    assert failed_rules(make_df(r2={"Age": "22"})) == {"QC06": 1}


def test_duplicate_id_marks_every_occurrence():
    df = make_df(r3={"Employee_ID": "1"}, r4={"Employee_ID": "1"})  # ID 1 três vezes
    assert failed_rules(df) == {"QC02": 3}


# ---------------------------------------------------------------- casos de borda
@pytest.mark.parametrize(
    ("age", "years", "ok"),
    [("23", "5", True), ("22", "4", True), ("22", "5", False), ("18", "0", True)],
)
def test_admission_age_boundary(age, years, ok):
    hire = {"0": "2024-01-01", "4": "2020-01-01", "5": "2019-09-04"}[years]
    df = make_df(1, r0={"Age": age, "Years_At_Company": years, "Hire_Date": hire})
    assert (evaluate_rule(RULES_BY_ID["QC06"], df).failed == 0) is ok


@pytest.mark.parametrize(("age", "ok"), [("18", True), ("70", True), ("17", False), ("71", False)])
def test_age_range_is_inclusive(age, ok):
    df = make_df(1, r0={"Age": age, "Years_At_Company": "0", "Hire_Date": "2024-01-01"})
    assert (evaluate_rule(RULES_BY_ID["QC04"], df).failed == 0) is ok


def test_tenure_exact_anniversary_counts_full_year():
    # 2019-09-05 → 2024-09-04 = 1826 dias → 1826 // 365 = 5
    df = make_df(1, r0={"Hire_Date": "2019-09-05", "Years_At_Company": "5"})
    assert evaluate_rule(RULES_BY_ID["QC05"], df).status == STATUS_PASS


def test_missing_inputs_are_not_evaluated_by_consistency_rules():
    df = make_df(3, r0={"Hire_Date": ""}, r1={"Age": ""})
    by_id = {r.id: r for r in run_checks(df)}
    assert by_id["QC05"].evaluated == 2 and by_id["QC05"].failed == 0
    assert by_id["QC06"].evaluated == 2 and by_id["QC06"].failed == 0
    assert by_id["QC01"].failed == 2   # a ausência é cobrada pela completude


def test_null_id_is_not_evaluated_for_uniqueness():
    df = make_df(3, r0={"Employee_ID": ""}, r1={"Employee_ID": ""})
    qc02 = evaluate_rule(RULES_BY_ID["QC02"], df)
    assert qc02.evaluated == 1 and qc02.failed == 0


def test_empty_dataset_reports_no_data_instead_of_100_percent():
    empty = normalize(pd.DataFrame(columns=list(BASE_ROW)))
    results = run_checks(empty)
    assert {r.status for r in results} == {STATUS_EMPTY}
    assert summarize(results)["overall_conformity"] is None


def test_missing_column_raises_clear_error():
    with pytest.raises(KeyError, match="Department"):
        run_checks(make_df().drop(columns=["Department"]))


# ---------------------------------------------------------------- status consolidado
@pytest.mark.parametrize(
    ("override", "verdict"),
    [
        ({}, "LIBERADA"),
        ({"Gender": "X"}, "LIBERADA COM RESSALVAS"),   # QC03 não crítica
        ({"Department": ""}, "BLOQUEADA"),              # QC01 crítica
    ],
)
def test_verdict_depends_on_rule_criticality(override, verdict):
    assert summarize(run_checks(make_df(r0=override)))["verdict"] == verdict


def test_threshold_allows_small_tolerance_on_non_critical_rules():
    # 1 falha em 200 = 99,5% ≥ meta de 99% → QC03 aprovada mesmo com 1 reprovação
    r = evaluate_rule(RULES_BY_ID["QC03"], make_df(200, r0={"Gender": "X"}))
    assert r.failed == 1 and r.status == STATUS_PASS
    # o mesmo defeito em base de 50 = 98% → reprovada
    assert evaluate_rule(RULES_BY_ID["QC03"], make_df(50, r0={"Gender": "X"})).status == STATUS_FAIL


# ---------------------------------------------------------------- paridade SQL × pandas
def test_sql_file_has_one_query_per_rule():
    queries = load_sql_queries()
    assert set(RULES_BY_ID) <= set(queries)


@pytest.mark.parametrize(
    "overrides",
    [
        {},
        {"r0": {"Department": ""}, "r1": {"Employee_ID": "3"}},
        {"r2": {"Gender": "M"}, "r3": {"Age": "99"}, "r4": {"Years_At_Company": "9"}},
        {"r5": {"Age": "22"}, "r6": {"Hire_Date": "2030-01-01"}, "r7": {"Monthly_Salary": "x"}},
    ],
)
def test_sql_and_pandas_agree(overrides):
    df = make_df(10, **overrides)
    results = run_checks(df)
    assert all(sql_matches(results, run_sql_checks(df)).values())


# ---------------------------------------------------------------- saída
def test_report_contains_required_columns():
    results = run_checks(make_df())
    md = render_markdown(results, summarize(results), "x.csv")
    for header in ("Regra", "Dimensão", "Avaliados", "Aprovados", "Reprovados",
                   "Conformidade", "Status"):
        assert header in md


def test_cli_writes_report_and_json(tmp_path):
    csv_path = tmp_path / "d.csv"
    pd.DataFrame([dict(BASE_ROW, Employee_ID=str(i)) for i in range(1, 6)]).to_csv(csv_path,
                                                                                  index=False)
    rc = main(["--data", str(csv_path), "--report", str(tmp_path / "r.md"),
               "--json", str(tmp_path / "r.json")])
    assert rc == 0
    payload = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert payload["summary"]["verdict"] == "LIBERADA" and payload["rows"] == 5
    assert "Relatório de Qualidade" in (tmp_path / "r.md").read_text(encoding="utf-8")


def test_cli_strict_mode_fails_on_blocked_dataset(tmp_path):
    csv_path = tmp_path / "d.csv"
    rows = [dict(BASE_ROW, Employee_ID="1"), dict(BASE_ROW, Employee_ID="1")]
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    assert main(["--data", str(csv_path), "--strict"]) == 1
    assert main(["--data", str(csv_path)]) == 0


def test_load_dataset_reads_csv_as_text_then_normalizes(tmp_path):
    p = tmp_path / "d.csv"
    pd.DataFrame([dict(BASE_ROW, Age=" 41 ")]).to_csv(p, index=False)
    df = load_dataset(p)
    assert df.loc[0, "Age"] == 41 and str(df.loc[0, "Hire_Date"].date()) == "2019-09-04"
