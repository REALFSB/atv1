"""Validação de qualidade de dados (Aula 9 · US11).

Aplica seis regras de negócio sobre a base de funcionários usada pelo projeto
(esquema do dataset Kaggle "Extended Employee Performance and Productivity Data"):

| ID   | Dimensão     | Regra                                                         |
|------|--------------|---------------------------------------------------------------|
| QC01 | Completude   | Campos obrigatórios preenchidos                               |
| QC02 | Unicidade    | Employee_ID não se repete                                     |
| QC03 | Validade     | Categorias dentro do domínio permitido                        |
| QC04 | Validade     | Valores numéricos dentro da faixa de negócio                  |
| QC05 | Consistência | Years_At_Company coerente com Hire_Date na data de referência |
| QC06 | Consistência | Idade na admissão (Age − Years_At_Company) ≥ 18 anos          |

Há dois motores com a mesma semântica: pandas (`run_checks`) e SQL
(`sql/quality_checks.sql`, executado em SQLite por `run_sql_checks`).
Os testes exigem que ambos produzam exatamente os mesmos números.

Uso:
    python -m src.validate --data data/sample_data.csv \
        --report reports/quality_report.md --json reports/quality_results.json
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections.abc import Callable, Sequence
from contextlib import closing
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SQL = ROOT / "sql" / "quality_checks.sql"

# Data de extração da base. Os valores de Hire_Date do Kaggle têm o mesmo horário
# (08:03:05.556036) e o maior é 2024-09-03, o que indica geração em 2024-09-04.
# Com essa data, Years_At_Company = dias_desde_admissão // 365 em 100% da base real.
REFERENCE_DATE = pd.Timestamp("2024-09-04")
MIN_ADMISSION_AGE = 18

REQUIRED_COLUMNS = [
    "Employee_ID", "Department", "Gender", "Age", "Hire_Date",
    "Years_At_Company", "Monthly_Salary", "Resigned",
]
NUMERIC_COLUMNS = [
    "Employee_ID", "Age", "Years_At_Company", "Performance_Score", "Monthly_Salary",
    "Work_Hours_Per_Week", "Projects_Handled", "Overtime_Hours", "Sick_Days",
    "Remote_Work_Frequency", "Team_Size", "Training_Hours", "Promotions",
    "Employee_Satisfaction_Score",
]
DOMAINS: dict[str, set[str]] = {
    "Department": {"Customer Support", "Engineering", "Finance", "HR", "IT",
                   "Legal", "Marketing", "Operations", "Sales"},
    "Gender": {"Female", "Male", "Other"},
    "Education_Level": {"High School", "Bachelor", "Master", "PhD"},
    "Job_Title": {"Analyst", "Consultant", "Developer", "Engineer", "Manager",
                  "Specialist", "Technician"},
    "Resigned": {"True", "False"},
}
# (mínimo, máximo) inclusivos
RANGES: dict[str, tuple[float, float]] = {
    "Age": (18, 70),
    "Years_At_Company": (0, 60),
    "Performance_Score": (1, 5),
    "Employee_Satisfaction_Score": (1.0, 5.0),
    "Monthly_Salary": (1, 100_000),
    "Work_Hours_Per_Week": (1, 80),
    "Sick_Days": (0, 365),
}

STATUS_PASS = "APROVADA"  # noqa: S105 (status de regra, não é senha)
STATUS_FAIL = "REPROVADA"
STATUS_EMPTY = "SEM DADOS"


# --------------------------------------------------------------------------- modelo
@dataclass(frozen=True)
class Rule:
    id: str
    name: str
    dimension: str
    description: str
    threshold: float          # conformidade mínima exigida (0–1)
    critical: bool            # crítica = bloqueia o uso da base no pipeline
    check: Callable[[pd.DataFrame], tuple[pd.Series, pd.Series]] = field(repr=False)


@dataclass
class RuleResult:
    id: str
    name: str
    dimension: str
    threshold: float
    critical: bool
    evaluated: int
    passed: int
    failed: int
    conformity: float | None
    status: str
    failed_ids: list = field(default_factory=list)


# --------------------------------------------------------------------------- carga
def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza tipos sem esconder defeitos: textos vazios viram ausentes,
    números inválidos viram ausentes e Hire_Date vira data ISO (AAAA-MM-DD)."""
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object or pd.api.types.is_string_dtype(out[col]):
            out[col] = out[col].astype("string").str.strip().replace("", pd.NA)
    for col in NUMERIC_COLUMNS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")
    if "Hire_Date" in out.columns:
        parsed = pd.to_datetime(out["Hire_Date"], errors="coerce", format="ISO8601")
        out["Hire_Date"] = parsed.dt.normalize()
    if "Resigned" in out.columns:
        out["Resigned"] = out["Resigned"].astype("string").str.strip()
    return out


def load_dataset(path: str | Path) -> pd.DataFrame:
    return normalize(pd.read_csv(path, dtype=str, keep_default_na=True))


def _require(df: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise KeyError(f"Colunas ausentes para validação: {missing}")


# --------------------------------------------------------------------------- regras
# Cada check devolve (máscara de avaliados, máscara de aprovados).
def check_completeness(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    _require(df, REQUIRED_COLUMNS)
    evaluated = pd.Series(True, index=df.index)
    return evaluated, df[REQUIRED_COLUMNS].notna().all(axis=1)


def check_uniqueness(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    _require(df, ["Employee_ID"])
    evaluated = df["Employee_ID"].notna()
    dup = df["Employee_ID"].duplicated(keep=False) & evaluated
    return evaluated, ~dup


def check_domain(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    _require(df, list(DOMAINS))
    ok = pd.Series(True, index=df.index)
    for col, allowed in DOMAINS.items():
        values = df[col]
        ok &= values.isna() | values.isin(allowed)
    return pd.Series(True, index=df.index), ok.astype(bool)


def check_ranges(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    _require(df, list(RANGES))
    ok = pd.Series(True, index=df.index)
    for col, (lo, hi) in RANGES.items():
        values = df[col]
        ok &= values.isna() | values.between(lo, hi)
    return pd.Series(True, index=df.index), ok.astype(bool)


def check_tenure_vs_hire_date(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    _require(df, ["Hire_Date", "Years_At_Company"])
    evaluated = df["Hire_Date"].notna() & df["Years_At_Company"].notna()
    days = (REFERENCE_DATE - df["Hire_Date"]).dt.days
    expected = days // 365
    ok = (days >= 0) & (expected == df["Years_At_Company"])
    return evaluated, (ok.fillna(False).astype(bool)) | ~evaluated


def check_admission_age(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    _require(df, ["Age", "Years_At_Company"])
    evaluated = df["Age"].notna() & df["Years_At_Company"].notna()
    ok = (df["Age"] - df["Years_At_Company"]) >= MIN_ADMISSION_AGE
    return evaluated, (ok.fillna(False).astype(bool)) | ~evaluated


RULES: list[Rule] = [
    Rule("QC01", "Campos obrigatórios preenchidos", "Completude",
         "Employee_ID, Department, Gender, Age, Hire_Date, Years_At_Company, "
         "Monthly_Salary e Resigned não podem estar vazios.", 1.00, True, check_completeness),
    Rule("QC02", "Employee_ID único", "Unicidade",
         "Cada funcionário aparece uma única vez; todas as ocorrências de um ID "
         "repetido são reprovadas.", 1.00, True, check_uniqueness),
    Rule("QC03", "Categorias no domínio permitido", "Validade",
         "Department, Gender, Education_Level, Job_Title e Resigned só aceitam "
         "os valores do catálogo.", 0.99, False, check_domain),
    Rule("QC04", "Valores numéricos na faixa de negócio", "Validade",
         "Age 18–70, Years_At_Company 0–60, Performance_Score 1–5, Satisfação 1–5, "
         "Salário 1–100.000, Horas/semana 1–80, Sick_Days 0–365.", 0.99, False, check_ranges),
    Rule("QC05", "Tempo de casa coerente com a admissão", "Consistência",
         "Years_At_Company = (2024-09-04 − Hire_Date) em dias // 365, e Hire_Date "
         "não pode ser posterior à data de referência.", 0.99, False, check_tenure_vs_hire_date),
    Rule("QC06", "Admissão com maioridade", "Consistência",
         "Age − Years_At_Company ≥ 18: ninguém pode ter sido admitido antes dos 18 anos.",
         0.99, False, check_admission_age),
]
RULES_BY_ID = {r.id: r for r in RULES}


# --------------------------------------------------------------------------- execução
def conformity_status(passed: int, evaluated: int, threshold: float) -> tuple[float | None, str]:
    if evaluated == 0:
        return None, STATUS_EMPTY
    conf = passed / evaluated
    return conf, STATUS_PASS if conf >= threshold else STATUS_FAIL


def evaluate_rule(rule: Rule, df: pd.DataFrame, max_ids: int = 20) -> RuleResult:
    evaluated_mask, pass_mask = rule.check(df)
    evaluated = int(evaluated_mask.sum())
    failed_mask = evaluated_mask & ~pass_mask
    failed = int(failed_mask.sum())
    passed = evaluated - failed
    conf, status = conformity_status(passed, evaluated, rule.threshold)
    ids = df.loc[failed_mask, "Employee_ID"] if "Employee_ID" in df else pd.Series(dtype=float)
    failed_ids = [None if pd.isna(v) else int(v) for v in ids.head(max_ids)]
    return RuleResult(rule.id, rule.name, rule.dimension, rule.threshold, rule.critical,
                      evaluated, passed, failed, conf, status, failed_ids)


def run_checks(df: pd.DataFrame, rules: Sequence[Rule] = RULES) -> list[RuleResult]:
    return [evaluate_rule(rule, df) for rule in rules]


def summarize(results: Sequence[RuleResult]) -> dict:
    evaluated = sum(r.evaluated for r in results)
    passed = sum(r.passed for r in results)
    approved = sum(r.status == STATUS_PASS for r in results)
    critical_fail = [r.id for r in results if r.critical and r.status != STATUS_PASS]
    other_fail = [r.id for r in results if not r.critical and r.status != STATUS_PASS]
    if critical_fail:
        verdict = "BLOQUEADA"
    elif other_fail:
        verdict = "LIBERADA COM RESSALVAS"
    else:
        verdict = "LIBERADA"
    worst = min((r for r in results if r.conformity is not None),
                key=lambda r: (r.conformity, -r.failed), default=None)
    return {
        "rules_total": len(results),
        "rules_approved": approved,
        "rules_failed": len(results) - approved,
        "checks_evaluated": evaluated,
        "checks_passed": passed,
        "overall_conformity": (passed / evaluated) if evaluated else None,
        "critical_failures": critical_fail,
        "other_failures": other_fail,
        "verdict": verdict,
        "worst_rule": worst.id if worst else None,
    }


# --------------------------------------------------------------------------- SQL
_NAME_RE = re.compile(r"^--\s*name:\s*(\S+)\s*$", re.MULTILINE)


def load_sql_queries(path: str | Path = DEFAULT_SQL) -> dict[str, str]:
    """Lê consultas nomeadas (`-- name: QC01`) de um arquivo .sql."""
    text = Path(path).read_text(encoding="utf-8")
    parts = _NAME_RE.split(text)
    return {parts[i]: parts[i + 1].strip().rstrip(";") for i in range(1, len(parts), 2)}


def to_sqlite(df: pd.DataFrame, conn: sqlite3.Connection, table: str = "employees") -> None:
    staged = df.copy()
    if "Hire_Date" in staged:
        staged["Hire_Date"] = staged["Hire_Date"].dt.strftime("%Y-%m-%d")
    staged = staged.astype(object).where(staged.notna(), None)
    staged.to_sql(table, conn, index=False, if_exists="replace")


def run_sql_checks(df: pd.DataFrame, sql_path: str | Path = DEFAULT_SQL) -> dict[str, dict]:
    """Executa as consultas QC01–QC06 em SQLite em memória sobre a base normalizada."""
    queries = load_sql_queries(sql_path)
    out: dict[str, dict] = {}
    with closing(sqlite3.connect(":memory:")) as conn:
        to_sqlite(df, conn)
        for rule_id in RULES_BY_ID:
            row = conn.execute(queries[rule_id]).fetchone()
            evaluated, passed, failed = (int(v or 0) for v in row)
            out[rule_id] = {"evaluated": evaluated, "passed": passed, "failed": failed}
    return out


def sql_matches(results: Sequence[RuleResult], sql: dict[str, dict]) -> dict[str, bool]:
    return {r.id: sql[r.id] == {"evaluated": r.evaluated, "passed": r.passed,
                                "failed": r.failed} for r in results}


# --------------------------------------------------------------------------- relatório
def _pct(v: float | None) -> str:
    return "—" if v is None else f"{v * 100:.2f}%".replace(".", ",")


def render_markdown(results: Sequence[RuleResult], summary: dict, dataset: str,
                    parity: dict[str, bool] | None = None, n_rows: int | None = None) -> str:
    lines = [
        "# Relatório de Qualidade dos Dados",
        "",
        f"- **Base avaliada:** `{dataset}`"
        + (f" ({n_rows} registros)" if n_rows is not None else ""),
        f"- **Data de referência das regras de consistência:** {REFERENCE_DATE.date()}",
        "- **Gerado por:** `python -m src.validate` "
        "(valores calculados na execução, não editados à mão)",
        "",
        "## Resultado por regra",
        "",
        "| ID | Regra | Dimensão | Avaliados | Aprovados | Reprovados "
        "| Conformidade | Meta | Status |"
        + (" SQL = pandas |" if parity else ""),
        "|---|---|---|---:|---:|---:|---:|---:|---|" + ("---|" if parity else ""),
    ]
    for r in results:
        crit = " (crítica)" if r.critical else ""
        row = (f"| {r.id} | {r.name}{crit} | {r.dimension} | {r.evaluated} | {r.passed} | "
               f"{r.failed} | {_pct(r.conformity)} | {_pct(r.threshold)} | **{r.status}** |")
        if parity:
            row += " sim |" if parity[r.id] else " **NÃO** |"
        lines.append(row)
    lines += [
        "",
        "## Consolidado",
        "",
        f"- Regras aprovadas: **{summary['rules_approved']} de {summary['rules_total']}**",
        f"- Regras reprovadas: **{summary['rules_failed']}**"
        + (f" ({', '.join(summary['critical_failures'] + summary['other_failures'])})"
           if summary["rules_failed"] else ""),
        f"- Verificações (registro × regra) avaliadas: {summary['checks_evaluated']} · "
        f"aprovadas: {summary['checks_passed']}",
        f"- **Conformidade geral:** {_pct(summary['overall_conformity'])} "
        "(soma dos aprovados ÷ soma dos avaliados, todas as regras)",
        f"- **Status final da base:** **{summary['verdict']}**",
        f"- Pior regra (menor conformidade): {summary['worst_rule']}",
        "",
        "Critério do status final: qualquer regra crítica (meta 100%) reprovada → "
        "**BLOQUEADA** (a base não entra no pipeline); só regras não críticas reprovadas → "
        "**LIBERADA COM RESSALVAS**; todas aprovadas → **LIBERADA**.",
        "",
        "## Registros reprovados (até 20 IDs por regra)",
        "",
    ]
    for r in results:
        if r.failed:
            ids = ", ".join("vazio" if i is None else str(i) for i in r.failed_ids)
            more = f" … (+{r.failed - len(r.failed_ids)})" if r.failed > len(r.failed_ids) else ""
            lines.append(f"- **{r.id}** ({r.failed}): {ids}{more}")
    if not any(r.failed for r in results):
        lines.append("- Nenhum registro reprovado.")
    lines.append("")
    return "\n".join(lines)


def build_payload(results, summary, dataset, parity, n_rows) -> dict:
    return {
        "dataset": dataset,
        "rows": n_rows,
        "reference_date": str(REFERENCE_DATE.date()),
        "summary": summary,
        "sql_parity": parity,
        "rules": [asdict(r) for r in results],
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Valida a qualidade da base de funcionários")
    ap.add_argument("--data", default=str(ROOT / "data" / "sample_data.csv"))
    ap.add_argument("--report", help="caminho do relatório Markdown")
    ap.add_argument("--json", help="caminho do resultado em JSON (lido pelo dashboard)")
    ap.add_argument("--sql", default=str(DEFAULT_SQL))
    ap.add_argument("--no-sql", action="store_true", help="não executa a conferência SQL")
    ap.add_argument("--strict", action="store_true",
                    help="retorna código 1 se a base ficar BLOQUEADA (uso como gate de CI)")
    a = ap.parse_args(argv)

    df = load_dataset(a.data)
    results = run_checks(df)
    summary = summarize(results)
    parity = None if a.no_sql else sql_matches(results, run_sql_checks(df, a.sql))
    try:
        label = Path(a.data).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        label = Path(a.data).name
    report = render_markdown(results, summary, label, parity, len(df))
    print(report)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(report, encoding="utf-8")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(build_payload(results, summary, label, parity, len(df)),
                                           indent=2, ensure_ascii=False), encoding="utf-8")
    if parity is not None and not all(parity.values()):
        print("ERRO: SQL e pandas divergiram em", [k for k, v in parity.items() if not v],
              file=sys.stderr)
        return 2
    if a.strict and summary["verdict"] == "BLOQUEADA":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
