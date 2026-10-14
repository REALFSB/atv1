"""Engenharia de atributos. Única definição de features, compartilhada por treino
e serving — evita a divergência treino/serving citada na Aula 5."""
from __future__ import annotations

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC = [
    "tenure_months", "distance_km", "overtime_hours_week", "prior_absences_30d",
    "productivity_pct", "day_of_week", "is_monday_or_friday", "overtime_high",
]
CATEGORICAL = ["sector", "shift"]
FEATURE_COLUMNS = NUMERIC + CATEGORICAL
OVERTIME_HIGH_THRESHOLD = 10.0  # horas extras/semana


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Função pura: devolve uma cópia com os atributos derivados."""
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["day_of_week"] = out["date"].dt.dayofweek
    out["is_monday_or_friday"] = out["day_of_week"].isin([0, 4]).astype(int)
    out["overtime_high"] = (out["overtime_hours_week"] >= OVERTIME_HIGH_THRESHOLD).astype(int)
    return out


def feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return add_features(df)[FEATURE_COLUMNS]


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])
