"""Linhagem de dados: compara a base Kaggle original com a versão "otimizada".

Gera reports/data_lineage.md com o que mudou, quanto mudou e o efeito no modelo.
Precisa das duas bases (ficam fora do Git):

    python scripts/compare_bases.py \
        --original data/raw/Extended_Employee_Performance_and_Productivity_Data.csv \
        --derived  data/raw/Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ["Age", "Years_At_Company", "Performance_Score", "Monthly_Salary",
           "Work_Hours_Per_Week", "Projects_Handled", "Overtime_Hours", "Remote_Work_Frequency",
           "Team_Size", "Training_Hours", "Promotions", "Employee_Satisfaction_Score"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt(v: float, d: int = 3) -> str:
    return f"{round(float(v), d) + 0.0:.{d}f}".replace(".", ",")


def main() -> int:
    import sys
    sys.path.insert(0, str(ROOT))
    from src.data.employees import normalize_employees
    from src.ml.kaggle_risk import train_employee_model

    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True)
    ap.add_argument("--derived", required=True)
    ap.add_argument("--out", default=str(ROOT / "reports" / "data_lineage.md"))
    a = ap.parse_args()
    po, pn = Path(a.original), Path(a.derived)
    o_txt, n_txt = pd.read_csv(po, dtype=str), pd.read_csv(pn, dtype=str)
    same_shape = o_txt.shape == n_txt.shape and list(o_txt.columns) == list(n_txt.columns)
    diff = (o_txt != n_txt)
    changed_cols = {c: int(v) for c, v in diff.sum().items() if v}
    rows_changed = int(diff.any(axis=1).sum())

    o, n = pd.read_csv(po), pd.read_csv(pn)
    corr = pd.DataFrame({"original": o[NUMERIC].corrwith(o["Sick_Days"]),
                         "otimizada": n[NUMERIC].corrwith(n["Sick_Days"])})
    corr = corr.reindex(corr["otimizada"].abs().sort_values(ascending=False).index)
    same_value = int((o["Sick_Days"] == n["Sick_Days"]).sum())
    m_o = train_employee_model(normalize_employees(o)).metrics
    m_n = train_employee_model(normalize_employees(n)).metrics

    L = [
        "# Linhagem de dados — base original × base \"otimizada\"",
        "",
        "> Gerado por `python scripts/compare_bases.py`. Governança (DAMA-DMBOK, linhagem e "
        "proveniência): toda versão derivada de uma fonte precisa dizer o que mudou e por quê.",
        "",
        "## Arquivos",
        "",
        "| Papel | Arquivo | Linhas | SHA-256 |",
        "|---|---|---:|---|",
        f"| Original (Kaggle) | `{po.name}` | {len(o)} | `{sha256(po)[:16]}…` |",
        f"| Derivada | `{pn.name}` | {len(n)} | `{sha256(pn)[:16]}…` |",
        "",
        "## O que mudou",
        "",
        f"- Mesmas linhas, mesma ordem e mesmas colunas: **{'sim' if same_shape else 'não'}**.",
        "- Colunas alteradas: **"
        + ", ".join(f"`{c}` ({v} linhas)" for c, v in changed_cols.items()) + "**.",
        f"- Linhas com alguma alteração: **{rows_changed} de {len(o)}** "
        f"({fmt(rows_changed / len(o) * 100, 1)}%).",
        f"- `Sick_Days` igual ao original em apenas {same_value} linhas "
        f"({fmt(same_value / len(o) * 100, 1)}%): perto do acaso para 15 valores possíveis "
        "(0 a 14), ou seja, a coluna foi **gerada de novo**, não corrigida.",
        f"- Média de `Sick_Days`: {fmt(o['Sick_Days'].mean(), 2)} → "
        f"{fmt(n['Sick_Days'].mean(), 2)}; desvio-padrão {fmt(o['Sick_Days'].std(), 2)} → "
        f"{fmt(n['Sick_Days'].std(), 2)}. A distribuição foi preservada; a **relação com as "
        "outras colunas** não.",
        "",
        "## Correlação de `Sick_Days` com as demais colunas numéricas",
        "",
        "| Coluna | Original | Otimizada |",
        "|---|---:|---:|",
    ]
    L += [f"| `{c}` | {fmt(r.original)} | {fmt(r.otimizada)} |" for c, r in corr.iterrows()]
    L += [
        "",
        "Na base original nenhuma correlação passa de 0,01 em módulo. Na derivada, "
        "`Sick_Days` passa a depender de horas extras, jornada e (negativamente) "
        "da satisfação.",
        "",
        "## Efeito no modelo de risco (mesmo código, mesma semente)",
        "",
        "| Métrica | Base original | Base otimizada | Meta |",
        "|---|---:|---:|---:|",
        f"| ROC-AUC | {fmt(m_o['roc_auc'])} | {fmt(m_n['roc_auc'])} | ≥ 0,700 |",
        f"| Recall | {fmt(m_o['recall'])} | {fmt(m_n['recall'])} | ≥ 0,600 |",
        f"| Precisão (limiar 0,5) | {fmt(m_o['precision'])} | {fmt(m_n['precision'])} | — |",
        f"| Precisão no top 10% | {fmt(m_o['precision_top10pct'])} | "
        f"{fmt(m_n['precision_top10pct'])} | — |",
        f"| Atinge a meta da US2 | {'sim' if m_o['meets_targets'] else 'não'} | "
        f"{'sim' if m_n['meets_targets'] else 'não'} | |",
        "",
        "## Leitura",
        "",
        "1. Na base original o modelo é equivalente a sortear (AUC ≈ 0,50): não há sinal de "
        "afastamento nas outras colunas.",
        "2. A melhora para AUC > 0,9 vem **inteiramente** da regeneração do alvo. O modelo está "
        "reaprendendo a regra usada para criar a coluna, não descobrindo um padrão de "
        "absenteísmo real.",
        "3. Uso aceitável: **demonstração do pipeline** com base semi-sintética, "
        "declarada como tal "
        "em todo lugar onde o número aparece (painel, relatórios, apresentação).",
        "4. Uso **não** aceitável: apresentar o AUC como resultado em dados reais do Kaggle.",
        "5. Falta registrar **quem** gerou a coluna e **com qual regra**. Sem isso, a linhagem "
        "fica incompleta (ver `docs/05-dados-reais.md`).",
        "",
    ]
    Path(a.out).write_text("\n".join(L), encoding="utf-8")
    print("Gerado:", a.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
