"""Gera `paineis/dashboard-data.js` (window.DASH_DATA), lido pelos 4 painéis.

Recalcula a base Extended a partir do CSV informado e reaproveita os agregados
congelados das bases HR Dashboard e Employee Productivity
(`data/dashboard_sources_snapshot.json`), cujos CSVs não estão no repositório.

Uso:
    python -m src.dashboard \
        --data data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .data.employees import SICK_HIGH_DAYS, normalize_employees

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "dashboard_sources_snapshot.json"
OUT = ROOT / "paineis" / "dashboard-data.js"

# métrica do painel -> coluna do esquema unificado
METRICS = {
    "prod": "productivity_index", "hours": "weekly_hours", "ot": "overtime_hours",
    "sat": "satisfaction", "proj": "projects", "train": "training_hours",
    "remote": "remote_pct", "sick": "sick_days", "salary": "monthly_salary",
    "tenure": "tenure_months",
}
YEAR_METRICS = ("prod", "ot", "sat")
UNIFIED_COLUMNS = [
    "employee_id", "source", "department", "job_title", "education_level", "age",
    "tenure_months", "monthly_salary", "weekly_hours", "overtime_hours", "training_hours",
    "projects", "satisfaction", "performance_score", "remote_pct", "team_size",
    "promotions", "sick_days", "has_label", "productivity_index",
]


def _pair(series: pd.Series) -> list:
    s = series.dropna()
    return [round(float(s.sum()), 3), int(s.size)]


def aggregate_extended(df: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    by_dept, by_year = [], []
    for dept, g in df.groupby("department", sort=True):
        row = {"source": "extended", "department": dept, "n": int(len(g))}
        row.update({k: _pair(g[c]) for k, c in METRICS.items()})
        row["sick_high"] = int((g["sick_days"] >= SICK_HIGH_DAYS).sum())
        row["resigned"] = int(g["resigned"].fillna(False).astype(bool).sum())
        by_dept.append(row)
    for year, g in df.dropna(subset=["hire_year"]).groupby("hire_year", sort=True):
        row = {"source": "extended", "year": int(year), "n": int(len(g))}
        row.update({k: _pair(g[METRICS[k]]) for k in YEAR_METRICS})
        by_year.append(row)
    return by_dept, by_year


def quality_block(df: pd.DataFrame, snap: dict) -> dict:
    ext = df.assign(source="extended", has_label=df["resigned"].notna())
    rows = len(ext) + snap["rows"]
    nulls = {}
    for col in UNIFIED_COLUMNS:
        n_ext = int(ext[col].isna().sum()) if col in ext else len(ext)
        nulls[col] = n_ext + snap["null_counts"].get(col, 0)
    return {
        "linhas": rows,
        "com_rotulo": int(ext["has_label"].sum()) + snap["labeled_rows"],
        "nulos_pct": {c: round(n / rows * 100, 1) for c, n in nulls.items()},
        "completude_pct": round(100 - sum(nulls.values()) / (rows * len(nulls)) * 100, 1),
    }


def build(raw: pd.DataFrame, snap: dict, now: datetime | None = None) -> dict:
    df = normalize_employees(raw)
    by_dept, by_year = aggregate_extended(df)
    now = now or datetime.now(timezone.utc)
    return {
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "params": snap["params"],
        "sources": {"extended": {"label": "Extended Employee Performance", "linhas": len(df)},
                    **snap["sources"]},
        "quality": quality_block(df, snap),
        "by_dept": by_dept + snap["by_dept"],
        "by_year": by_year + snap["by_year"],
    }


def write_js(data: dict, path: Path = OUT) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("window.DASH_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n",
                    encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gera paineis/dashboard-data.js")
    ap.add_argument("--data", required=True, help="CSV Extended Employee Performance")
    ap.add_argument("--snapshot", default=str(SNAPSHOT))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    snap = json.loads(Path(a.snapshot).read_text(encoding="utf-8"))
    data = build(pd.read_csv(a.data), snap)
    print("Gerado:", write_js(data, Path(a.out)), "·", data["quality"]["linhas"], "linhas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
