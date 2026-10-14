"""Engenharia de atributos. Única definição de features, compartilhada por treino
e serving — evita a divergência treino/serving citada na Aula 5."""
from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = [
    "tenure_months", "monthly_salary", "weekly_hours", "overtime_hours", "training_hours",
    "projects", "satisfaction", "performance_score", "remote_pct", "team_size", "promotions",
    "overtime_ratio", "low_satisfaction",
]
CATEGORICAL = ["department", "job_title", "education_level"]
FEATURE_COLUMNS = NUMERIC + CATEGORICAL
# Fora das features por decisão de governança: idade e gênero (risco de discriminação),
# sick_days (gera o rótulo) e qualquer dado de saúde (LGPD).
LOW_SATISFACTION = 2.0


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Função pura: devolve uma cópia com os atributos derivados."""
    out = df.copy()
    out["overtime_ratio"] = out["overtime_hours"] / out["weekly_hours"].clip(lower=1)
    out["low_satisfaction"] = (out["satisfaction"] <= LOW_SATISFACTION).astype(int)
    return out


def feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return add_features(df)[FEATURE_COLUMNS]


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
