"""Modelo de risco de absenteísmo por funcionário, treinado na base de funcionários.

Alvo: `sick_high` = 11 ou mais dias de afastamento no ano (`Sick_Days >= 11`).
Diferenças em relação ao modelo operacional (`src.ml.train`, dados diários sintéticos):
* a base tem 1 linha por funcionário e nenhum eixo temporal de ausências, então o
  teste é um holdout estratificado (25%, semente fixa), não um split temporal;
* registros em quarentena pela QC06 ficam fora do treino e do ranking;
* `Gender` e `Age` não entram como atributos.

⚠️ Sobre a base "otimizada": em `Extended_..._2_otimizado.csv` a coluna `Sick_Days`
foi regenerada e passou a depender de horas extras, jornada e satisfação (ver
`reports/data_lineage.md`). Um AUC alto nessa base mede o quanto o modelo recupera
essa regra, não o absenteísmo de uma operação real.

Uso:
    python -m src.ml.kaggle_risk \
        --data data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ..data.employees import SICK_HIGH_DAYS, load_employees
from ..serving.risk import risk_band, top_factors
from ..validate import load_dataset, run_checks, summarize
from .train import TrainResult, meets_targets

NUMERIC = [
    "tenure_months", "monthly_salary", "weekly_hours", "overtime_hours", "overtime_ratio",
    "training_hours", "projects", "satisfaction", "performance_score", "remote_pct",
    "team_size", "promotions",
]
CATEGORICAL = ["department", "job_title", "education_level"]
FEATURES = NUMERIC + CATEGORICAL
TARGET = "sick_high"
TOP_SHARE = 0.10   # precisão no top 10% de risco: o que o gestor efetivamente olha


def build_pipeline() -> Pipeline:
    prep = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
    return Pipeline([("prep", prep),
                     ("clf", LogisticRegression(max_iter=1000, class_weight="balanced"))])


def usable(df: pd.DataFrame) -> pd.DataFrame:
    """Remove quarentena (QC06) e linhas sem alvo/atributo."""
    ok = df[df["qc06_ok"]]
    return ok.dropna(subset=FEATURES + [TARGET]).reset_index(drop=True)


def precision_at_top(y_true: np.ndarray, proba: np.ndarray, share: float = TOP_SHARE) -> float:
    k = max(1, int(len(proba) * share))
    idx = np.argsort(-proba)[:k]
    return float(np.asarray(y_true)[idx].mean())


def train_employee_model(df: pd.DataFrame, test_fraction: float = 0.25,
                         seed: int = 42) -> TrainResult:
    data = usable(df)
    train, test = train_test_split(data, test_size=test_fraction, random_state=seed,
                                   stratify=data[TARGET])
    pipe = build_pipeline().fit(train[FEATURES], train[TARGET])
    proba = pipe.predict_proba(test[FEATURES])[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "model": "logistic",
        "target": f"Sick_Days >= {SICK_HIGH_DAYS}",
        "split": f"holdout estratificado {int(test_fraction * 100)}% (seed {seed})",
        "roc_auc": float(roc_auc_score(test[TARGET], proba)),
        "recall": float(recall_score(test[TARGET], pred)),
        "precision": float(precision_score(test[TARGET], pred, zero_division=0)),
        "precision_top10pct": precision_at_top(test[TARGET].to_numpy(), proba),
        "positive_rate_test": float(test[TARGET].mean()),
        "n_train": int(len(train)), "n_test": int(len(test)),
        "quarantined_qc06": int((~df["qc06_ok"]).sum()),
    }
    metrics["meets_targets"] = meets_targets(metrics)
    return TrainResult(pipe, metrics)


def score_employees(df: pd.DataFrame, model) -> pd.DataFrame:
    data = usable(df)
    proba = model.predict_proba(data[FEATURES])[:, 1]
    out = data[["employee_id", "department", "job_title"]].copy()
    out["risk"] = proba.round(4)
    out["band"] = [risk_band(p) for p in proba]
    out["factors"] = top_factors(model, data[FEATURES])
    out = out.sort_values(["risk", "employee_id"], ascending=[False, True]).reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


def export_js(ranked: pd.DataFrame, metrics: dict, path: str, dataset: str,
              top: int = 200) -> str:
    """Grava `window.RISCO_DATA` para o painel Equipes & Escalas (só IDs pseudonimizados)."""
    semi = "otimizado" in dataset
    payload = {
        "source": "kaggle_semissintetico" if semi else "kaggle",
        "source_label": ("BASE KAGGLE COM SICK_DAYS REGERADO (SEMI-SINTÉTICA)" if semi
                         else "BASE KAGGLE (100 mil funcionários rotulados)"),
        "dataset": dataset,
        "target": metrics["target"],
        "metrics": {k: metrics[k] for k in ("roc_auc", "recall", "precision",
                                            "precision_top10pct")},
        "meets_targets": metrics["meets_targets"],
        "total": int(len(ranked)),
        "quarantined": metrics["quarantined_qc06"],
        "counts": {k: int(v) for k, v in ranked["band"].value_counts().items()},
        "ranking": json.loads(ranked.head(top).rename(columns={"employee_id": "id"})
                              .to_json(orient="records", force_ascii=False)),
    }
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("window.RISCO_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Treina e aplica o modelo por funcionário")
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", default="artifacts/kaggle")
    ap.add_argument("--web-out", default="paineis/risco-data.js")
    ap.add_argument("--top", type=int, default=200)
    ap.add_argument("--skip-quality-gate", action="store_true",
                    help="treina mesmo com a base BLOQUEADA (não recomendado)")
    a = ap.parse_args(argv)
    # Portão de qualidade (SBAR, recomendação 2): base BLOQUEADA não treina.
    verdict = summarize(run_checks(load_dataset(a.data)))["verdict"]
    print("Qualidade da base:", verdict)
    if verdict == "BLOQUEADA" and not a.skip_quality_gate:
        print("ERRO: regra crítica de qualidade reprovada; rode python -m src.validate "
              f"--data {a.data} para ver o detalhe.")
        return 1
    df = load_employees(a.data)
    result = train_employee_model(df)
    result.metrics["dataset"] = Path(a.data).name
    os.makedirs(a.out, exist_ok=True)
    joblib.dump(result.pipeline, os.path.join(a.out, "model.joblib"))
    with open(os.path.join(a.out, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(result.metrics, f, indent=2, ensure_ascii=False)
    ranked = score_employees(df, result.pipeline)
    ranked.to_csv(os.path.join(a.out, "ranking.csv"), index=False, encoding="utf-8-sig")
    export_js(ranked, result.metrics, a.web_out, Path(a.data).name, a.top)
    print(json.dumps(result.metrics, indent=2, ensure_ascii=False))
    print("Painel:", a.web_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
