"""Testes da integração com o Firestore usando um banco falso em memória
(não precisam de internet nem de credenciais)."""
import numpy as np
import pandas as pd
import pytest

from src.data.firebase import BATCH_SIZE, FirestoreSource, upsert_operations
from src.data.ingest import (REQUIRED_COLUMNS, SENSITIVE_COLUMNS, SyntheticSource,
                             load_operations, make_source)
from src.ml.train import train_model
from src.serving.firebase_export import export_risk_firestore
from src.serving.risk import predict_risk


class FakeDoc:
    def __init__(self, data): self._d = data
    def to_dict(self): return dict(self._d)


class FakeCol:
    def __init__(self, store, path, flt=None):
        self.store, self.path, self.flt = store, path, flt
    def document(self, doc_id): return FakeRef(self.store, f"{self.path}/{doc_id}")
    def where(self, *args, filter=None):
        assert filter is not None, "use where(filter=FieldFilter(...))"
        return FakeCol(self.store, self.path, filter)
    def stream(self):
        for k, v in sorted(self.store.items()):
            if k.startswith(self.path + "/") and "/" not in k[len(self.path) + 1:]:
                if self.flt is None or v[self.flt.field_path] >= self.flt.value:
                    yield FakeDoc(v)


class FakeRef:
    def __init__(self, store, path): self.store, self.path = store, path
    def set(self, data): self.store[self.path] = data
    def collection(self, name): return FakeCol(self.store, f"{self.path}/{name}")


class FakeBatch:
    def __init__(self, db): self.db, self.ops = db, []
    def set(self, ref, data): self.ops.append((ref, data))
    def commit(self):
        self.db.batch_sizes.append(len(self.ops))
        for ref, data in self.ops:
            ref.set(data)


class FakeDb:
    def __init__(self): self.store, self.batch_sizes = {}, []
    def collection(self, name): return FakeCol(self.store, name)
    def batch(self): return FakeBatch(self)


@pytest.fixture
def ops():
    return load_operations(SyntheticSource(n_employees=30, n_days=40))  # 1200 linhas


def test_upsert_writes_one_doc_per_operator_day_in_batches(ops):
    db = FakeDb()
    assert upsert_operations(ops, db=db) == len(ops)
    assert len(db.store) == len(ops)
    assert max(db.batch_sizes) <= BATCH_SIZE and sum(db.batch_sizes) == len(ops)
    doc_id, doc = next(iter(db.store.items()))
    assert doc_id == f"operations/{doc['employee_id']}_{doc['date']}"
    assert isinstance(doc["date"], str) and len(doc["date"]) == 10
    # tipos nativos do Python (o cliente do Firestore rejeita numpy)
    assert all(not isinstance(v, np.generic) for v in doc.values())


def test_upsert_is_idempotent(ops):
    db = FakeDb()
    upsert_operations(ops, db=db)
    upsert_operations(ops, db=db)
    assert len(db.store) == len(ops)


def test_upsert_only_contract_columns_never_sensitive(ops):
    ops = ops.assign(**{c: "x" for c in SENSITIVE_COLUMNS})
    db = FakeDb()
    upsert_operations(ops, db=db)
    assert all(set(v) == set(REQUIRED_COLUMNS) for v in db.store.values())


def test_upsert_rejects_raw_employee_ids(ops):
    raw = ops.assign(employee_id="OP0001")
    with pytest.raises(ValueError, match="pseudonimizado"):
        upsert_operations(raw, db=FakeDb())


def test_source_roundtrip_does_not_rehash_ids(ops):
    db = FakeDb()
    upsert_operations(ops, db=db)
    back = load_operations(FirestoreSource(db=db))
    assert set(back["employee_id"]) == set(ops["employee_id"])
    assert len(back) == len(ops)


def test_source_since_filters_by_date(ops):
    db = FakeDb()
    upsert_operations(ops, db=db)
    cut = sorted(ops["date"].unique())[20]
    back = FirestoreSource(since=str(cut)[:10], db=db).load()
    assert back["date"].min() >= pd.Timestamp(cut)
    assert len(back) < len(ops)


def test_source_empty_collection_gives_clear_error():
    with pytest.raises(ValueError, match="src.data.sync"):
        FirestoreSource(db=FakeDb()).load()


def test_make_source_firestore_is_lazy():
    src = make_source("firestore", since="2026-09-01")  # não conecta nem pede credenciais
    assert isinstance(src, FirestoreSource) and src.since == "2026-09-01"


def test_train_from_firestore_source(ops):
    db = FakeDb()
    upsert_operations(load_operations(SyntheticSource()), db=db)
    result = train_model(FirestoreSource(db=db))
    assert result.metrics["meets_targets"] is True


def test_export_ranking_to_firestore(tmp_path, ops):
    result = train_model(SyntheticSource())
    ranked = predict_risk(ops[ops["date"] == ops["date"].max()], result.pipeline, with_factors=True)
    db = FakeDb()
    run_id = export_risk_firestore(ranked, "synthetic", str(tmp_path / "nao-existe.json"),
                                   ref_date=ops["date"].max(), db=db)
    run = db.store[f"risk_runs/{run_id}"]
    assert run["n"] == len(ranked) and sum(run["counts"].values()) == len(ranked)
    first = db.store[f"risk_runs/{run_id}/ranking/00001"]
    assert first["rank"] == 1 and set(first) >= {"id", "risk", "band", "factors"}
    assert all(not isinstance(v, np.generic) for v in first.values())
