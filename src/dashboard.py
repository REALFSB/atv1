"""Dados do painel: agrega as 3 bases do Kaggle e grava `dashboard-data.js`.

Responsabilidade única (SRP): transformar a base unificada (`harmonize.build_unified`)
em agregados que as páginas HTML consomem. Nenhum número do painel é digitado à mão:
tudo vem dos CSVs em `data/raw/`.

Os agregados guardam **soma e contagem** (não só a média) por fonte × departamento.
Assim o navegador combina as fontes (ou filtra uma só) com a média ponderada correta.

LGPD: só saem agregados por grupo. Grupos com menos de `MIN_GROUP` pessoas têm os
indicadores de afastamento suprimidos (dado ligado à saúde).
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone

import pandas as pd

from .harmonize import FILES, REF_DATE, build_unified, quality_report

MIN_GROUP = 5          # grupo menor que isso não expõe afastamento (LGPD)
HIGH_ABSENCE_DAYS = 11  # mesmo limiar do rótulo do modelo (ingest.HIGH_ABSENCE_DAYS)

# Parâmetros de negócio (NÃO são dados): ficam num só lugar e vão para o painel.
PARAMS = {
    "jornada_padrao_h": 40,
    "limite_absenteismo_dias": HIGH_ABSENCE_DAYS,
    # status do atingimento (% do alvo): >= superada | >= na meta | >= atenção | crítica
    "faixas": {"superada": 105, "na_meta": 95, "atencao": 85},
    # Catálogo de metas. `sentido`: "max" = quanto maior melhor; "min" = quanto menor melhor.
    "metas": [
        {"id": "prod", "nome": "Índice de produtividade", "curto": "produtividade", "detalhe": "Desempenho 1–5 convertido para 0–100",
         "alvo": 50.0, "sentido": "max", "unidade": "pts", "casas": 1},
        {"id": "sat", "nome": "Satisfação dos funcionários", "curto": "satisfação", "detalhe": "Escala 1–5 (ponto médio = 3)",
         "alvo": 3.0, "sentido": "max", "unidade": "/5", "casas": 2},
        {"id": "ot", "nome": "Horas extras por funcionário", "curto": "horas extras", "detalhe": "Média de horas extras registradas",
         "alvo": 15.0, "sentido": "min", "unidade": "h", "casas": 1},
        {"id": "sick", "nome": "Dias de afastamento por ano", "curto": "afastamento", "detalhe": "Média de dias de afastamento (Sick_Days)",
         "alvo": 7.0, "sentido": "min", "unidade": "dias", "casas": 1},
    ],
}

# métrica -> coluna da base unificada
METRIC_COLUMNS = {
    "prod": "productivity_index", "hours": "weekly_hours", "ot": "overtime_hours", "sat": "satisfaction",
    "proj": "projects", "train": "training_hours", "remote": "remote_pct", "sick": "sick_days",
    "salary": "monthly_salary", "tenure": "tenure_months",
}
SENSITIVE_METRICS = {"sick"}

SOURCE_LABELS = {
    "extended": "Extended Employee Performance",
    "hr_dashboard": "HR Dashboard",
    "productivity": "Employee Productivity",
}


def with_productivity_index(df: pd.DataFrame) -> pd.DataFrame:
    """Desempenho 1–5 -> índice 0–100 (inverso exato de `harmonize._pct_to_1_5`)."""
    out = df.copy()
    out["productivity_index"] = (out["performance_score"] - 1) * 25
    return out


def _stat(series: pd.Series) -> list[float | int]:
    """[soma, contagem] dos valores não nulos (permite média ponderada no navegador)."""
    s = series.dropna()
    return [round(float(s.sum()), 3), int(s.size)]


def group_rows(df: pd.DataFrame, keys: list[str]) -> list[dict]:
    rows = []
    for key, g in df.groupby(keys, dropna=True, observed=True):
        key = key if isinstance(key, tuple) else (key,)
        row = dict(zip(keys, (k.item() if hasattr(k, "item") else k for k in key)))
        row["n"] = int(len(g))
        suppress = len(g) < MIN_GROUP
        for name, col in METRIC_COLUMNS.items():
            row[name] = [0.0, 0] if (name in SENSITIVE_METRICS and suppress) else _stat(g[col])
        sick = g["sick_days"].dropna()
        row["sick_high"] = 0 if suppress else int((sick >= HIGH_ABSENCE_DAYS).sum())
        rows.append(row)
    return rows


def resigned_by_group(data_dir: str) -> dict[str, int]:
    """Desligados por departamento: só a base Extended tem o campo `Resigned`."""
    path = os.path.join(data_dir, FILES["extended"])
    if not os.path.exists(path):
        return {}
    raw = pd.read_csv(path, usecols=["Department", "Resigned"])
    raw["Resigned"] = raw["Resigned"].astype(str).str.lower().eq("true")
    return {str(k): int(v) for k, v in raw.groupby("Department")["Resigned"].sum().items()}


def admission_year(df: pd.DataFrame) -> pd.Series:
    """Ano de admissão = data de referência da base − tempo de casa (meses)."""
    ref = df["source"].map(lambda s: pd.Timestamp(REF_DATE[s]))
    delta = pd.to_timedelta(df["tenure_months"] * 30.44, unit="D")
    return (ref - delta).dt.year


def build_dashboard_data(data_dir: str) -> dict:
    df = with_productivity_index(build_unified(data_dir))
    df["department"] = df["department"].astype(str)
    q = quality_report(df)

    by_dept = group_rows(df, ["source", "department"])
    resigned = resigned_by_group(data_dir)
    for r in by_dept:
        r["resigned"] = resigned.get(r["department"], 0) if r["source"] == "extended" else 0

    cohort = df[df["source"].isin(["extended", "hr_dashboard"])].copy()
    cohort["year"] = admission_year(cohort)
    cohort = cohort.dropna(subset=["year"])
    cohort["year"] = cohort["year"].astype(int)
    by_year = [{k: v for k, v in r.items() if k in ("source", "year", "n", "prod", "ot", "sat")}
               for r in group_rows(cohort, ["source", "year"])]

    completude = 100 - float(df.drop(columns=["has_label"]).isna().mean().mean() * 100)
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "params": PARAMS,
        "sources": {s: {"label": SOURCE_LABELS[s], "linhas": int(n)} for s, n in q["por_fonte"].items()},
        "quality": {"linhas": q["linhas"], "com_rotulo": q["com_rotulo"], "nulos_pct": q["nulos_pct"],
                    "completude_pct": round(completude, 1)},
        "by_dept": by_dept,
        "by_year": by_year,
    }


def export_dashboard_js(data: dict, path: str = "dashboard-data.js") -> str:
    """Grava `window.DASH_DATA = {...};` (estático: funciona na Vercel e abrindo o HTML direto)."""
    with open(path, "w", encoding="utf-8") as f:
        f.write("window.DASH_DATA = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera os dados agregados lidos pelo painel (dashboard-data.js)")
    ap.add_argument("--path", default="data/raw", help="pasta com os 3 CSVs do Kaggle")
    ap.add_argument("--out", default="dashboard-data.js")
    a = ap.parse_args()
    data = build_dashboard_data(a.path)
    print("Fontes:", {k: v["linhas"] for k, v in data["sources"].items()})
    print("Grupos fonte×departamento:", len(data["by_dept"]), "· coortes:", len(data["by_year"]))
    print("Painel:", export_dashboard_js(data, a.out))


if __name__ == "__main__":
    main()
