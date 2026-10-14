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
    "employee_id", "department", "job_title", "education_level", "tenure_months",
    "monthly_salary", "weekly_hours", "overtime_hours", "training_hours", "projects",
    "satisfaction", "performance_score", "remote_pct", "team_size", "promotions", "absent",
]
HIGH_ABSENCE_DAYS = 11  # absent = 1 se faltou/afastou ≥ 11 dias no ano (≈ quartil superior)
# LGPD: dados de saúde/hábitos não entram no pipeline (RNF4 / US4).
SENSITIVE_COLUMNS = [
    "reason_for_absence", "health_condition", "medical_certificate",
    "social_drinker", "social_smoker", "sick_days",  # sick_days gera o rótulo; nunca é feature (vazamento/saúde)
    "name", "gender", "age",  # identificação direta e atributos de risco de discriminação
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


class KaggleHRSource(DataSource):
    """Bases do Kaggle (3 CSVs em `data_dir`), harmonizadas por `harmonize.build_unified`.
    Devolve só as linhas rotuladas, já com `absent` (sick_days ≥ HIGH_ABSENCE_DAYS)."""

    def __init__(self, data_dir: str, threshold: int = HIGH_ABSENCE_DAYS):
        self.data_dir, self.threshold = data_dir, threshold

    def load(self) -> pd.DataFrame:
        from .harmonize import build_unified
        df = build_unified(self.data_dir)
        df = df[df["has_label"]].copy()
        df["absent"] = (df["sick_days"] >= self.threshold).astype(int)
        return df[REQUIRED_COLUMNS + ["sick_days", "age"]]


class SyntheticSource(DataSource):
    """Dados sintéticos com sinal embutido (desenvolvimento e testes do pipeline).
    NÃO representa a operação real: métricas obtidas aqui são só de pipeline."""

    DEPARTMENTS = ["E-commerce", "Logística", "Atendimento", "Qualidade"]
    TITLES = ["Operador", "Analista", "Líder", "Auxiliar"]
    EDUCATION = ["High School", "Bachelor", "Master"]

    def __init__(self, n_employees: int = 3000, seed: int = 42, threshold: int = HIGH_ABSENCE_DAYS):
        self.n, self.seed, self.threshold = n_employees, seed, threshold

    def load(self) -> pd.DataFrame:
        rng = np.random.default_rng(self.seed)
        n = self.n
        df = pd.DataFrame({
            "employee_id": [f"OP{i:05d}" for i in range(n)],
            "department": rng.choice(self.DEPARTMENTS, n, p=[.28, .34, .23, .15]),
            "job_title": rng.choice(self.TITLES, n),
            "education_level": rng.choice(self.EDUCATION, n, p=[.4, .5, .1]),
            "tenure_months": rng.integers(1, 120, n),
            "monthly_salary": rng.normal(4200, 900, n).clip(1800).round(0),
            "weekly_hours": rng.integers(36, 50, n),
            "overtime_hours": rng.integers(0, 30, n),
            "training_hours": rng.integers(0, 100, n),
            "projects": rng.integers(0, 40, n),
            "satisfaction": rng.uniform(1, 5, n).round(2),
            "performance_score": rng.integers(1, 6, n),
            "remote_pct": rng.integers(0, 101, n),
            "team_size": rng.integers(2, 20, n),
            "promotions": rng.integers(0, 3, n),
        })
        lam = np.exp(1.85 + 0.04 * (df["overtime_hours"] - 14.5) - 0.22 * (df["satisfaction"] - 3)
                     - 0.003 * (df["tenure_months"] - 60) + 0.2 * (df["department"] == "Atendimento"))
        sick = np.clip(rng.poisson(lam), 0, 14)
        df["absent"] = (sick >= self.threshold).astype(int)
        return df[REQUIRED_COLUMNS]


def make_source(kind: str, path: str | None = None) -> DataSource:
    """Fábrica usada pelas CLIs: trocar a fonte não exige mudar train/serve."""
    if kind == "synthetic":
        return SyntheticSource()
    if kind == "kaggle" and path:
        return KaggleHRSource(path)
    if kind == "csv" and path:
        return CsvSource(path)
    raise ValueError("Use --source synthetic | kaggle --path <pasta> | csv --path <arquivo>")


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
