"""Treino. Depende da abstração `DataSource` (DIP) e de um registro de modelos
(OCP): novos algoritmos entram com `register_model`, sem editar `train_model`."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Callable

import joblib
import pandas as pd
from sklearn.base import ClassifierMixin
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline

from .features import add_features, build_preprocessor, FEATURE_COLUMNS
from .ingest import DataSource, load_operations, make_source

# Metas de ML do backlog (US2 / RNF1)
TARGET_RECALL = 0.60
TARGET_AUC = 0.70

MODEL_REGISTRY: dict[str, Callable[[], ClassifierMixin]] = {
    "logistic": lambda: LogisticRegression(max_iter=1000, class_weight="balanced"),
    "gradient_boosting": lambda: GradientBoostingClassifier(random_state=42),
}


def register_model(name: str, factory: Callable[[], ClassifierMixin]) -> None:
    MODEL_REGISTRY[name] = factory


@dataclass
class TrainResult:
    pipeline: Pipeline
    metrics: dict


def split(df: pd.DataFrame, test_fraction: float = 0.25, seed: int = 42):
    """Divisão estratificada (as bases não têm data de ausência, logo não há split temporal)."""
    return train_test_split(df, test_size=test_fraction, random_state=seed, stratify=df["absent"])


def train_model(source: DataSource, model_name: str = "logistic",
                test_fraction: float = 0.25, salt: str | None = None) -> TrainResult:
    df = add_features(load_operations(source, salt))
    train, test = split(df, test_fraction)
    pipe = Pipeline([("prep", build_preprocessor()), ("clf", MODEL_REGISTRY[model_name]())])
    pipe.fit(train[FEATURE_COLUMNS], train["absent"])
    proba = pipe.predict_proba(test[FEATURE_COLUMNS])[:, 1]
    pred = (proba >= 0.5).astype(int)
    metrics = {
        "model": model_name,
        "roc_auc": float(roc_auc_score(test["absent"], proba)),
        "recall": float(recall_score(test["absent"], pred)),
        "precision": float(precision_score(test["absent"], pred, zero_division=0)),
        "absence_rate_test": float(test["absent"].mean()),
        "n_train": int(len(train)), "n_test": int(len(test)),
    }
    metrics["meets_targets"] = meets_targets(metrics)
    return TrainResult(pipe, metrics)


def meets_targets(metrics: dict) -> bool:
    return metrics["recall"] >= TARGET_RECALL and metrics["roc_auc"] >= TARGET_AUC


def save_artifacts(result: TrainResult, out_dir: str = "artifacts") -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "model.joblib")
    joblib.dump(result.pipeline, path)
    with open(os.path.join(out_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(result.metrics, f, indent=2, ensure_ascii=False)
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Treina o modelo de risco de ausência")
    ap.add_argument("--source", default="synthetic", choices=["synthetic", "kaggle", "csv"])
    ap.add_argument("--path")
    ap.add_argument("--model", default="logistic", choices=list(MODEL_REGISTRY))
    ap.add_argument("--out", default="artifacts")
    a = ap.parse_args()
    result = train_model(make_source(a.source, a.path), a.model)
    print(json.dumps(result.metrics, indent=2, ensure_ascii=False))
    print("Modelo salvo em:", save_artifacts(result, a.out))
    if not result.metrics["meets_targets"]:
        print(f"AVISO: abaixo da meta (recall ≥ {TARGET_RECALL}, AUC ≥ {TARGET_AUC}). "
              "Não use este ranking para decisões (US2/RNF1).")


if __name__ == "__main__":
    main()
