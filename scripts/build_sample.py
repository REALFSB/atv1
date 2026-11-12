"""Gera data/sample_data.csv de forma determinística a partir da base Kaggle.

Amostra = 30 registros:
  * Employee_ID 1–24: copiados sem alteração da base original;
  * Employee_ID 25–30: copiados e com UM defeito injetado cada (documentado abaixo
    e em data/README.md), para que toda regra de qualidade tenha caso reprovado.

Uso (a base bruta fica fora do Git):
    python scripts/build_sample.py \
        --raw data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
N_CLEAN = 24

# Employee_ID original -> (coluna, novo valor, regra que deve reprovar)
INJECTIONS: dict[str, tuple[str, str, str]] = {
    "25": ("Department", "", "QC01 completude: departamento vazio"),
    "26": ("Employee_ID", "7", "QC02 unicidade: ID 7 duplicado"),
    "27": ("Gender", "M", "QC03 domínio: 'M' fora do catálogo"),
    "28": ("Performance_Score", "7", "QC04 faixa: nota de desempenho 7 (máx. 5)"),
    "29": ("Years_At_Company", "+3", "QC05 consistência: tempo de casa 3 anos acima da admissão"),
    "30": ("Monthly_Salary", "N/D", "QC01 completude: salário não numérico (vira ausente)"),
}


def build(raw: Path, out: Path) -> list[dict]:
    with raw.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = [r for _, r in zip(range(N_CLEAN + len(INJECTIONS)), reader, strict=False)]
    for row in rows[N_CLEAN:]:
        col, value, _ = INJECTIONS[row["Employee_ID"]]
        if value.startswith("+"):
            value = str(int(row[col]) + int(value[1:]))
        row[col] = value
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", default=str(ROOT / "data" / "sample_data.csv"))
    a = ap.parse_args()
    print(f"{len(build(Path(a.raw), Path(a.out)))} registros gravados em {a.out}")
