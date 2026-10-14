"""Serving: aplica o modelo a dados novos. Isolado do treino (latência, RNF2).
Depende do protocolo mínimo `Predictor` (ISP/DIP), não de uma classe de modelo."""
from __future__ import annotations

import argparse
import json
import os
from typing import Protocol

import joblib
import numpy as np
import pandas as pd

from .features import FEATURE_COLUMNS, add_features
from .ingest import load_operations, make_source

BAND_HIGH = 0.60
BAND_MEDIUM = 0.40


class Predictor(Protocol):
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray: ...


def load_model(path: str = "artifacts/model.joblib") -> Predictor:
    return joblib.load(path)


def risk_band(p: float) -> str:
    return "Alta" if p >= BAND_HIGH else "Média" if p >= BAND_MEDIUM else "Baixa"


def predict_risk(df: pd.DataFrame, model: Predictor, with_factors: bool = False) -> pd.DataFrame:
    """US1: lista de operadores ordenada do maior para o menor risco de ausência."""
    feats = add_features(df)
    proba = model.predict_proba(feats[FEATURE_COLUMNS])[:, 1]
    out = feats[["employee_id", "sector", "shift"]].copy()
    out["risk"] = proba.round(4)
    out["band"] = [risk_band(p) for p in proba]
    if with_factors:
        out["top_factors"] = top_factors(model, feats[FEATURE_COLUMNS])
    out = out.sort_values("risk", ascending=False).reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


def top_factors(model, X: pd.DataFrame, k: int = 3) -> list[str]:
    """US6 (explicabilidade): fatores que mais elevam o risco de cada operador.
    Válido para modelos lineares; outros modelos retornam lista vazia."""
    steps = getattr(model, "named_steps", {})
    clf = steps.get("clf")
    if clf is None or not hasattr(clf, "coef_"):
        return [""] * len(X)
    Z = steps["prep"].transform(X)
    Z = Z.toarray() if hasattr(Z, "toarray") else np.asarray(Z)
    names = steps["prep"].get_feature_names_out()
    contrib = Z * clf.coef_[0]
    top = np.argsort(-contrib, axis=1)[:, :k]
    return [", ".join(names[j].split("__", 1)[-1] for j in row) for row in top]


def export_risk_csv(ranked: pd.DataFrame, path: str) -> str:
    """US5: exportação em CSV, sem tocar no código de treino."""
    ranked.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def export_risk_js(ranked: pd.DataFrame, path: str, source: str = "synthetic",
                   metrics_path: str = "artifacts/metrics.json") -> str:
    """Liga o modelo ao painel web: grava `window.RISCO_DATA` em um .js estático
    (funciona na Vercel e abrindo o HTML direto). Só IDs pseudonimizados saem daqui."""
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, encoding="utf-8") as f:
            metrics = json.load(f)
    rows = ranked.rename(columns={"employee_id": "id", "top_factors": "factors"})
    payload = {
        "source": source,
        "metrics": {k: metrics.get(k) for k in ("roc_auc", "recall", "precision")},
        "counts": ranked["band"].value_counts().to_dict(),
        "ranking": json.loads(rows.drop(columns=[c for c in ("date",) if c in rows]).to_json(orient="records")),
    }
    with open(path, "w", encoding="utf-8") as f:
        f.write("window.RISCO_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera a lista de risco de ausência do último dia")
    ap.add_argument("--model", default="artifacts/model.joblib")
    ap.add_argument("--source", default="synthetic", choices=["synthetic", "csv"])
    ap.add_argument("--path")
    ap.add_argument("--out", default="artifacts/ranking.csv")
    ap.add_argument("--web-out", default="risco-data.js", help="arquivo lido por equipes.html")
    a = ap.parse_args()
    df = load_operations(make_source(a.source, a.path))
    latest = df[df["date"] == df["date"].max()]
    ranked = predict_risk(latest, load_model(a.model), with_factors=True)
    print(ranked.head(10).to_string(index=False))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    print("CSV:", export_risk_csv(ranked, a.out))
    print("Painel:", export_risk_js(ranked, a.web_out, a.source))


if __name__ == "__main__":
    main()
