"""Smoke tests: o pipeline roda ponta a ponta com entradas fixas e versionadas.

1. Qualidade: data/sample_data.csv (30 registros, 6 defeitos documentados em
   data/README.md) → números exatos conhecidos. Se algum mudar, ou a amostra ou
   uma regra mudou, e o relatório precisa ser regenerado.
2. ML: ingest → train → serve com fonte sintética de semente fixa.
"""
import json
from pathlib import Path

import pytest

from src.validate import main as validate_main

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "sample_data.csv"

EXPECTED_FAILED = {"QC01": 2, "QC02": 2, "QC03": 1, "QC04": 1, "QC05": 1, "QC06": 1}


@pytest.mark.smoke
def test_quality_pipeline_on_fixed_sample(tmp_path):
    out_json, out_md = tmp_path / "q.json", tmp_path / "q.md"
    rc = validate_main(["--data", str(SAMPLE), "--json", str(out_json), "--report", str(out_md)])
    assert rc == 0  # sem --strict o pipeline conclui e só relata
    payload = json.loads(out_json.read_text(encoding="utf-8"))

    assert payload["rows"] == 30
    assert {r["id"]: r["failed"] for r in payload["rules"]} == EXPECTED_FAILED
    assert all(payload["sql_parity"].values())
    s = payload["summary"]
    assert (s["checks_evaluated"], s["checks_passed"]) == (180, 172)
    assert s["verdict"] == "BLOQUEADA"
    assert out_md.read_text(encoding="utf-8").count("| QC0") == 6


@pytest.mark.smoke
def test_committed_quality_report_matches_current_code(tmp_path):
    """O relatório versionado em reports/ precisa ser o resultado real da execução."""
    committed = json.loads((ROOT / "reports" / "quality_results.json").read_text(encoding="utf-8"))
    fresh_path = tmp_path / "fresh.json"
    validate_main(["--data", str(SAMPLE), "--json", str(fresh_path)])
    fresh = json.loads(fresh_path.read_text(encoding="utf-8"))
    assert committed["summary"] == fresh["summary"]
    assert committed["rules"] == fresh["rules"]


@pytest.mark.smoke
def test_ml_pipeline_end_to_end(tmp_path):
    from src.data.ingest import SyntheticSource, load_operations
    from src.ml.train import save_artifacts, train_model
    from src.serving.risk import export_risk_csv, load_model, predict_risk

    result = train_model(SyntheticSource(n_employees=40, n_days=30, seed=7))
    model_path = save_artifacts(result, str(tmp_path))
    today = load_operations(SyntheticSource(n_employees=40, n_days=30, seed=7))
    today = today[today["date"] == today["date"].max()]
    ranked = predict_risk(today, load_model(model_path))
    export_risk_csv(ranked, str(tmp_path / "ranking.csv"))
    assert len(ranked) == 40 and (tmp_path / "ranking.csv").exists()
