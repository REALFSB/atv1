"""Grava o ranking de risco no Firestore (coleções `risk_runs` e subcoleção `ranking`)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pandas as pd

from ..data.firebase import BATCH_SIZE, get_db

RISK_RUNS = "risk_runs"


def export_risk_firestore(ranked: pd.DataFrame, source: str = "synthetic",
                          metrics_path: str = "artifacts/metrics.json",
                          ref_date=None, db=None) -> str:
    """Uma execução = 1 documento em `risk_runs/{runId}` + N em `.../ranking/{posição}`.
    Devolve o runId. Só IDs pseudonimizados são gravados."""
    db = db or get_db()
    metrics = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, encoding="utf-8") as f:
            metrics = json.load(f)
    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    run = db.collection(RISK_RUNS).document(run_id)
    run.set({
        "created_at": now,
        "ref_date": pd.to_datetime(ref_date).strftime("%Y-%m-%d") if ref_date is not None else None,
        "source": source,
        "model": metrics.get("model"),
        "roc_auc": metrics.get("roc_auc"),
        "recall": metrics.get("recall"),
        "precision": metrics.get("precision"),
        "counts": {k: int(v) for k, v in ranked["band"].value_counts().items()},
        "n": int(len(ranked)),
    })
    rows = ranked.rename(columns={"employee_id": "id", "top_factors": "factors"}).to_dict("records")
    col = run.collection("ranking")
    for i in range(0, len(rows), BATCH_SIZE):
        batch = db.batch()
        for r in rows[i:i + BATCH_SIZE]:
            batch.set(col.document(f"{int(r['rank']):05d}"), r)
        batch.commit()
    return run_id
