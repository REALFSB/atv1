"""Integração com o Firebase (Cloud Firestore).

Regras do projeto:
* Só dados JÁ pseudonimizados e sem colunas sensíveis chegam ao Firestore (LGPD, US4).
* Gravação idempotente: o ID do documento é `<hash>_<AAAA-MM-DD>`; rodar de novo
  atualiza em vez de duplicar.
* `FirestoreSource` implementa `DataSource` (DIP): treino e serving não sabem de onde
  os dados vêm.
"""
from __future__ import annotations

import os

import pandas as pd

from .ingest import REQUIRED_COLUMNS, DataSource

OPERATIONS = "operations"
BATCH_SIZE = 500  # limite de escritas por lote no Firestore
DAILY_WRITE_QUOTA = 20_000  # cota gratuita (plano Spark)


def get_db():
    """Cliente do Firestore usando a chave de serviço em GOOGLE_APPLICATION_CREDENTIALS."""
    import firebase_admin
    from firebase_admin import credentials, firestore

    try:
        firebase_admin.get_app()
    except ValueError:
        cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path or not os.path.isfile(cred_path):
            raise RuntimeError(
                "Defina GOOGLE_APPLICATION_CREDENTIALS com o caminho do JSON da conta de serviço "
                "(Firebase Console > Configurações do projeto > Contas de serviço)."
            )
        firebase_admin.initialize_app(credentials.Certificate(cred_path))
    return firestore.client()


def _check_pseudonymized(df: pd.DataFrame) -> None:
    ids = df["employee_id"].astype(str)
    if not ids.str.fullmatch(r"[0-9a-f]{12}").all():
        raise ValueError(
            "employee_id não parece pseudonimizado (esperado hash de 12 caracteres hex). "
            "Passe os dados por load_operations() antes de gravar no Firestore."
        )


def upsert_operations(df: pd.DataFrame, collection: str = OPERATIONS, db=None) -> int:
    """Grava operações (um documento por operador/dia) em lotes de 500."""
    _check_pseudonymized(df)
    db = db or get_db()
    out = df[REQUIRED_COLUMNS].copy()  # só as colunas do contrato; nada sensível entra
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    col = db.collection(collection)
    records = out.to_dict("records")
    for i in range(0, len(records), BATCH_SIZE):
        batch = db.batch()
        for r in records[i:i + BATCH_SIZE]:
            batch.set(col.document(f"{r['employee_id']}_{r['date']}"), r)
        batch.commit()
    return len(records)


class FirestoreSource(DataSource):
    """Lê operações do Firestore. `since` (AAAA-MM-DD) limita as leituras: cada documento
    lido conta na cota diária (50 mil no plano Spark)."""

    already_pseudonymized = True  # load_operations não aplica o hash de novo

    def __init__(self, since: str | None = None, collection: str = OPERATIONS, db=None):
        self.since = pd.to_datetime(since).strftime("%Y-%m-%d") if since else None
        self.collection, self._db = collection, db

    def load(self) -> pd.DataFrame:
        from google.cloud.firestore_v1.base_query import FieldFilter

        query = (self._db or get_db()).collection(self.collection)
        if self.since:
            query = query.where(filter=FieldFilter("date", ">=", self.since))
        df = pd.DataFrame([d.to_dict() for d in query.stream()])
        if df.empty:
            raise ValueError(
                f"Nenhum documento encontrado em '{self.collection}'"
                + (f" a partir de {self.since}" if self.since else "")
                + ". Rode antes: python -m src.data.sync"
            )
        df["date"] = pd.to_datetime(df["date"])
        return df
