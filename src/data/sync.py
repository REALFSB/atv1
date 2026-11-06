"""Envia os dados tratados para o Firestore:  python -m src.data.sync [--dry-run]

Fluxo: fonte (CSV/sintética) → descarta sensíveis → valida → pseudonimiza → Firestore.
"""
from __future__ import annotations

import argparse

from .firebase import DAILY_WRITE_QUOTA, OPERATIONS, upsert_operations
from .ingest import load_operations, make_source


def main() -> None:
    ap = argparse.ArgumentParser(description="Sincroniza operações tratadas com o Firestore")
    ap.add_argument("--source", default="synthetic", choices=["synthetic", "csv"])
    ap.add_argument("--path", help="CSV de entrada (com --source csv)")
    ap.add_argument("--dry-run", action="store_true", help="só valida e mostra o resumo, não grava")
    a = ap.parse_args()

    df = load_operations(make_source(a.source, a.path))
    print(f"{len(df)} registros prontos | {df['employee_id'].nunique()} operadores | "
          f"{df['date'].min():%Y-%m-%d} a {df['date'].max():%Y-%m-%d}")
    if len(df) > DAILY_WRITE_QUOTA:
        print(f"ATENÇÃO: {len(df)} escritas passam da cota gratuita diária ({DAILY_WRITE_QUOTA}).")
    if a.dry_run:
        print("dry-run: nada foi gravado.")
        return
    n = upsert_operations(df)
    print(f"{n} documentos gravados/atualizados na coleção '{OPERATIONS}'.")


if __name__ == "__main__":
    main()
