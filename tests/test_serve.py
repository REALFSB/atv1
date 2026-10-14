import time

import pandas as pd
import pytest

from src.ingest import SyntheticSource, load_operations
from src.serve import export_risk_csv, predict_risk
from src.train import train_model


@pytest.fixture(scope="module")
def model():
    return train_model(SyntheticSource()).pipeline


@pytest.fixture(scope="module")
def today():
    return load_operations(SyntheticSource(n_employees=155, seed=7))


def test_ranking_is_sorted_desc_with_bands(model, today):
    """US1 – Dado dados carregados, quando gera a lista, então ordena do maior para o menor risco."""
    r = predict_risk(today, model)
    assert r["risk"].is_monotonic_decreasing and r["rank"].tolist() == list(range(1, len(r) + 1))
    assert set(r["band"]) <= {"Alta", "Média", "Baixa"}


def test_latency_under_5s_for_155_operators(model, today):  # RNF2
    t0 = time.perf_counter()
    predict_risk(today, model)
    assert time.perf_counter() - t0 < 5


def test_export_csv_keeps_all_rows(model, today, tmp_path):  # US5
    ranked = predict_risk(today, model)
    path = export_risk_csv(ranked, str(tmp_path / "r.csv"))
    back = pd.read_csv(path)
    assert len(back) == len(ranked) and {"rank", "risk", "band"} <= set(back.columns)


def test_top_factors_returns_three_per_operator(model, today):  # US6
    r = predict_risk(today, model, with_factors=True)
    assert all(len(f.split(", ")) == 3 for f in r["top_factors"])


def test_export_js_for_dashboard(model, today, tmp_path):  # integração com equipes.html
    import json
    from src.serve import export_risk_js
    ranked = predict_risk(today, model, with_factors=True)
    path = export_risk_js(ranked, str(tmp_path / "r.js"), metrics_path=str(tmp_path / "x.json"))
    txt = open(path, encoding="utf-8").read()
    assert txt.startswith("window.RISCO_DATA = ")
    data = json.loads(txt[len("window.RISCO_DATA = "):].rstrip(";\n"))
    assert len(data["ranking"]) == len(ranked) and data["ranking"][0]["rank"] == 1
    assert sum(data["counts"].values()) == len(ranked)
