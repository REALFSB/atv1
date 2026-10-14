import json

import pandas as pd
from sklearn.dummy import DummyClassifier

from src.ingest import DataSource, SyntheticSource
from src.train import (MODEL_REGISTRY, meets_targets, register_model, save_artifacts,
                       time_split, train_model)


def test_metrics_meet_targets_on_synthetic():  # US2 (métrica do modelo)
    r = train_model(SyntheticSource())
    assert r.metrics["meets_targets"] and r.metrics["recall"] >= 0.60 and r.metrics["roc_auc"] >= 0.70


def test_time_split_has_no_leakage(ops):
    from src.features import add_features
    tr, te = time_split(add_features(ops))
    assert tr["date"].max() < te["date"].min()


def test_dip_any_datasource_works():  # DIP/LSP: fonte substituível sem tocar no treino
    class InMemory(DataSource):
        def load(self) -> pd.DataFrame:
            return SyntheticSource(30, 30, seed=1).load()
    assert "roc_auc" in train_model(InMemory()).metrics


def test_ocp_new_model_without_editing_train_model():
    register_model("dummy", lambda: DummyClassifier(strategy="prior"))
    assert "roc_auc" in train_model(SyntheticSource(20, 20), "dummy").metrics
    MODEL_REGISTRY.pop("dummy")


def test_meets_targets_logic():
    assert not meets_targets({"recall": 0.5, "roc_auc": 0.9})


def test_save_artifacts(tmp_path):
    r = train_model(SyntheticSource(20, 20))
    save_artifacts(r, str(tmp_path))
    assert (tmp_path / "model.joblib").exists()
    assert "roc_auc" in json.loads((tmp_path / "metrics.json").read_text())
