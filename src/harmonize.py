"""Harmonização e mescla das bases brutas (Kaggle) em um único esquema.

Responsabilidade única: padronizar nomes/escalas/unidades, limpar e empilhar.
As três bases NÃO têm chave em comum (IDs de formatos diferentes, uma sem ID),
então a mescla é um *empilhamento* com coluna `source`, não um join linha a linha.
Só a base grande tem rótulo (`sick_days`); as demais ficam como `has_label=False`.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

FILES = {
    "extended": "Extended_Employee_Performance_and_Productivity_Data.csv",
    "hr_dashboard": "hr_dashboard_data.csv",
    "productivity": "employee_productivity.csv",
}
# Data de referência de cada arquivo (usada para calcular tempo de casa)
REF_DATE = {"extended": "2024-09-04", "hr_dashboard": "2023-08-02", "productivity": "2025-09-28"}
UNIFIED_COLUMNS = [
    "employee_id", "source", "department", "job_title", "education_level", "age",
    "tenure_months", "monthly_salary", "weekly_hours", "overtime_hours", "training_hours",
    "projects", "satisfaction", "performance_score", "remote_pct", "team_size",
    "promotions", "sick_days", "has_label",
]
# Faixas válidas: valores fora viram NaN (tratados na validação)
RANGES = {"age": (16, 75), "tenure_months": (0, 600), "monthly_salary": (500, 100000),
          "weekly_hours": (10, 80), "satisfaction": (1, 5), "performance_score": (1, 5),
          "remote_pct": (0, 100), "sick_days": (0, 366)}


def _pct_to_1_5(s: pd.Series) -> pd.Series:
    """Converte escala 0–100 para 1–5 (mesma escala da base grande)."""
    return 1 + 4 * s.clip(0, 100) / 100


def _months_between(start: pd.Series, ref: str) -> pd.Series:
    return ((pd.Timestamp(ref) - pd.to_datetime(start)).dt.days / 30.44).round()


def _from_extended(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "employee_id": "EXT-" + df["Employee_ID"].astype(str), "department": df["Department"],
        "job_title": df["Job_Title"], "education_level": df["Education_Level"], "age": df["Age"],
        "tenure_months": _months_between(df["Hire_Date"], REF_DATE["extended"]),
        "monthly_salary": df["Monthly_Salary"], "weekly_hours": df["Work_Hours_Per_Week"],
        "overtime_hours": df["Overtime_Hours"], "training_hours": df["Training_Hours"],
        "projects": df["Projects_Handled"], "satisfaction": df["Employee_Satisfaction_Score"],
        "performance_score": df["Performance_Score"], "remote_pct": df["Remote_Work_Frequency"],
        "team_size": df["Team_Size"], "promotions": df["Promotions"], "sick_days": df["Sick_Days"],
    })


def _from_hr_dashboard(df: pd.DataFrame) -> pd.DataFrame:
    # `Name` é dado pessoal direto: não é lido para o esquema (LGPD).
    # "Jan-20" = mês-ano de 2 dígitos (pandas: 00–68 → 20xx, 69–99 → 19xx).
    joined = pd.to_datetime(df["Joining Date"], format="%b-%y", errors="coerce")
    return pd.DataFrame({
        "employee_id": [f"HRD-{i:04d}" for i in range(len(df))], "department": df["Department"],
        "job_title": df["Position"], "age": df["Age"],
        "tenure_months": _months_between(joined, REF_DATE["hr_dashboard"]),
        "monthly_salary": df["Salary"] / 12, "projects": df["Projects Completed"],
        "satisfaction": _pct_to_1_5(df["Satisfaction Rate (%)"]),
        "performance_score": _pct_to_1_5(df["Productivity (%)"]),
    })


def _from_productivity(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "employee_id": "PRD-" + df["Employee_ID"].astype(str), "department": df["Department"],
        "tenure_months": df["Experience_Years"] * 12,  # experiência ≈ tempo de casa (aprox.)
        "monthly_salary": df["Salary_USD"] / 12, "weekly_hours": df["Avg_Weekly_Work_Hours"],
        "training_hours": df["Training_Hours"], "projects": df["Projects_Completed"],
        "performance_score": _pct_to_1_5(df["Productivity_Score"]),
    })


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza: texto padronizado, duplicados removidos, valores fora da faixa viram NaN."""
    out = df.copy()
    for c in ("department", "job_title", "education_level"):
        out[c] = out[c].astype("string").str.strip()
    out = out.drop_duplicates(subset=["source", "employee_id"]).reset_index(drop=True)
    for col, (lo, hi) in RANGES.items():
        out.loc[(out[col] < lo) | (out[col] > hi), col] = np.nan
    return out


def build_unified(data_dir: str) -> pd.DataFrame:
    """Lê os CSVs disponíveis em `data_dir` e devolve a base unificada e limpa."""
    parts = []
    for key, conv in (("extended", _from_extended), ("hr_dashboard", _from_hr_dashboard),
                      ("productivity", _from_productivity)):
        path = os.path.join(data_dir, FILES[key])
        if os.path.exists(path):
            part = conv(pd.read_csv(path))
            part.insert(1, "source", key)
            parts.append(part)
    if not parts:
        raise FileNotFoundError(f"Nenhum CSV conhecido em {data_dir}: {list(FILES.values())}")
    df = pd.concat(parts, ignore_index=True).reindex(columns=[c for c in UNIFIED_COLUMNS if c != "has_label"])
    df = clean(df)
    df["has_label"] = df["sick_days"].notna()
    return df[UNIFIED_COLUMNS]


def quality_report(df: pd.DataFrame) -> dict:
    return {
        "linhas": int(len(df)), "por_fonte": df["source"].value_counts().to_dict(),
        "com_rotulo": int(df["has_label"].sum()),
        "nulos_pct": (df.isna().mean() * 100).round(1).to_dict(),
    }
