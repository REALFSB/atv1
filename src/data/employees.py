"""Ingestão da base de funcionários (Kaggle *Extended Employee Performance and
Productivity Data*) no esquema unificado do DataTrack.

Usada pelo modelo por funcionário (`src.ml.kaggle_risk`) e pelo gerador do painel
(`src.dashboard`). Mesmas proteções da ingestão operacional (US3/US4):
* `Gender` e `Age` não viram atributos do modelo (atributos protegidos: evitar
  discriminação; `Age` só é lida para a checagem de consistência QC06);
* `Employee_ID` sai pseudonimizado (SHA-256 com sal);
* registros que reprovam a regra QC06 (admissão antes dos 18 anos) ficam em
  quarentena, conforme a decisão D4 da ata (`docs/meeting_minutes.md`).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..validate import MIN_ADMISSION_AGE, REFERENCE_DATE
from .ingest import pseudonymize

KAGGLE_COLUMN_MAP = {
    "Employee_ID": "employee_id", "Department": "department", "Job_Title": "job_title",
    "Education_Level": "education_level", "Age": "age", "Hire_Date": "hire_date",
    "Years_At_Company": "years_at_company", "Monthly_Salary": "monthly_salary",
    "Work_Hours_Per_Week": "weekly_hours", "Overtime_Hours": "overtime_hours",
    "Training_Hours": "training_hours", "Projects_Handled": "projects",
    "Employee_Satisfaction_Score": "satisfaction", "Performance_Score": "performance_score",
    "Remote_Work_Frequency": "remote_pct", "Team_Size": "team_size",
    "Promotions": "promotions", "Sick_Days": "sick_days", "Resigned": "resigned",
}
PROTECTED_COLUMNS = ["Gender"]          # descartada na leitura
SICK_HIGH_DAYS = 11                     # "absenteísmo alto" = 11+ dias de afastamento no ano
DAYS_PER_MONTH = 30.44                  # mesma conversão usada no painel desde a Aula 6


def normalize_employees(raw: pd.DataFrame) -> pd.DataFrame:
    """Converte o CSV do Kaggle para o esquema unificado (função pura)."""
    missing = [c for c in KAGGLE_COLUMN_MAP if c not in raw.columns]
    if missing:
        raise KeyError(f"Colunas ausentes na base de funcionários: {missing}")
    df = raw.drop(columns=[c for c in PROTECTED_COLUMNS if c in raw.columns])
    df = df.rename(columns=KAGGLE_COLUMN_MAP)[list(KAGGLE_COLUMN_MAP.values())].copy()
    hire = pd.to_datetime(df["hire_date"], errors="coerce", format="ISO8601")
    # dias completos entre a admissão (com horário) e a data de referência, em meses
    df["tenure_months"] = np.round((REFERENCE_DATE - hire).dt.days / DAYS_PER_MONTH)
    df["hire_year"] = hire.dt.year
    df["productivity_index"] = (df["performance_score"] - 1) * 25   # escala 1–5 → 0–100
    df["overtime_ratio"] = df["overtime_hours"] / df["weekly_hours"].replace(0, np.nan)
    df["resigned"] = df["resigned"].astype(str).str.strip().str.lower().map(
        {"true": True, "false": False})
    df["sick_high"] = (df["sick_days"] >= SICK_HIGH_DAYS).astype(int)
    df["qc06_ok"] = (df["age"] - df["years_at_company"]) >= MIN_ADMISSION_AGE
    return df


def load_employees(path: str, salt: str | None = None) -> pd.DataFrame:
    """Lê, normaliza e pseudonimiza. Não remove a quarentena: quem consome decide."""
    return pseudonymize(normalize_employees(pd.read_csv(path)), salt)
