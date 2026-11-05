"""Ingestão: carrega, valida e protege os dados brutos (requisitos de dados, Aula 4).

Responsabilidade única (SRP): obter dados confiáveis. Não faz feature nem treino.
Inversão de Dependência (DIP): quem consome dados depende de `DataSource`,
nunca de um CSV, banco ou API específicos.
"""
from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "employee_id", "date", "sector", "shift", "tenure_months", "distance_km",
    "overtime_hours_week", "prior_absences_30d", "productivity_pct", "absent",
]
# LGPD: dados de saúde/hábitos não entram no pipeline (RNF4 / US4).
SENSITIVE_COLUMNS = [
    "reason_for_absence", "health_condition", "medical_certificate",
    "social_drinker", "social_smoker",
]
MAX_NULL_RATE = 0.05  # requisito de dados: no máximo 5% de nulos por coluna (US3)


class DataQualityError(ValueError):
    """Dados fora do padrão mínimo de qualidade."""


class DataSource(ABC):
    """Abstração de fonte de dados. Toda fonte devolve o mesmo esquema."""

    @abstractmethod
    def load(self) -> pd.DataFrame:
        ...


class CsvSource(DataSource):
    """CSV local (ex.: base do Kaggle). `column_map` renomeia colunas originais
    para o esquema do DataTrack, sem tocar em nenhum outro módulo."""

    def __init__(self, path: str, column_map: dict[str, str] | None = None):
        self.path = path
        self.column_map = column_map or {}

    def load(self) -> pd.DataFrame:
        return pd.read_csv(self.path).rename(columns=self.column_map)


class SyntheticSource(DataSource):
    """Gera dados sintéticos no esquema do DataTrack (desenvolvimento e testes).
    NÃO representa a operação real: métricas obtidas aqui são só de pipeline."""

    SECTORS = ["E-commerce", "Logística", "Atendimento", "Qualidade"]
    SHIFTS = ["Manhã", "Tarde", "Noite"]

    def __init__(self, n_employees: int = 148, n_days: int = 60, seed: int = 42):
        self.n_employees, self.n_days, self.seed = n_employees, n_days, seed

    def load(self) -> pd.DataFrame:
        rng = np.random.default_rng(self.seed)
        n, d = self.n_employees, self.n_days
        emp = pd.DataFrame({
            "employee_id": [f"OP{i:04d}" for i in range(n)],
            "sector": rng.choice(self.SECTORS, n, p=[.28, .34, .23, .15]),
            "shift": rng.choice(self.SHIFTS, n),
            "tenure_months": rng.integers(1, 96, n),
            "distance_km": rng.uniform(1, 40, n).round(1),
            "propensity": rng.normal(0, 0.6, n),  # fator latente (não exportado)
        })
        dates = pd.bdate_range("2026-07-01", periods=d)
        df = emp.merge(pd.DataFrame({"date": dates}), how="cross")
        m = len(df)
        df["overtime_hours_week"] = rng.gamma(2.0, 3.0, m).round(1)
        df["productivity_pct"] = np.clip(rng.normal(93, 6, m), 60, 110).round(1)
        df["prior_absences_30d"] = rng.poisson(np.exp(-0.5 + df["propensity"]))
        dow = df["date"].dt.dayofweek
        logit = (-4.2 + 0.05 * df["distance_km"] + 0.06 * df["overtime_hours_week"]
                 + 0.45 * df["prior_absences_30d"] - 0.01 * df["tenure_months"]
                 + 0.5 * (dow == 0) + 0.4 * (dow == 4)
                 + 0.4 * (df["sector"] == "Atendimento") + df["propensity"])
        df["absent"] = (rng.random(m) < 1 / (1 + np.exp(-logit))).astype(int)
        return df.drop(columns="propensity")[REQUIRED_COLUMNS]


def make_source(kind: str, path: str | None = None) -> DataSource:
    """Fábrica usada pelas CLIs: trocar a fonte não exige mudar train/serve."""
    if kind == "synthetic":
        return SyntheticSource()
    if kind == "csv" and path:
        return CsvSource(path)
    raise ValueError("Use --source synthetic ou --source csv --path <arquivo>")


def validate(df: pd.DataFrame, max_null_rate: float = MAX_NULL_RATE) -> pd.DataFrame:
    """Rejeita dados que violam o requisito de qualidade (US3)."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise DataQualityError(f"Colunas obrigatórias ausentes: {missing}")
    rates = df[REQUIRED_COLUMNS].isna().mean()
    bad = rates[rates > max_null_rate]
    if not bad.empty:
        detalhe = ", ".join(f"{c} ({r:.1%} nulos)" for c, r in bad.items())
        raise DataQualityError(f"Colunas acima de {max_null_rate:.0%} de nulos: {detalhe}")
    if not df["absent"].dropna().isin([0, 1]).all():
        raise DataQualityError("Coluna 'absent' deve conter apenas 0 ou 1")
    return df


def pseudonymize(df: pd.DataFrame, salt: str | None = None) -> pd.DataFrame:
    """Troca employee_id por hash com sal (LGPD, US4). Determinístico: o mesmo
    operador recebe sempre o mesmo código, permitindo histórico sem identificar."""
    salt = salt or os.environ.get("DATATRACK_SALT", "dev-salt-troque-em-producao")
    out = df.copy()
    out["employee_id"] = out["employee_id"].astype(str).map(
        lambda v: hashlib.sha256(f"{salt}:{v}".encode()).hexdigest()[:12])
    return out


def load_operations(source: DataSource, salt: str | None = None) -> pd.DataFrame:
    """Caso de uso de ingestão: carregar → descartar sensíveis → validar → pseudonimizar."""
    df = source.load()
    df = df.drop(columns=[c for c in SENSITIVE_COLUMNS if c in df.columns])
    df = validate(df).dropna(subset=REQUIRED_COLUMNS).reset_index(drop=True)
    return pseudonymize(df, salt)
