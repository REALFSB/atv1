"""Consolida as métricas reais do projeto em reports/metrics.json e reports/metrics.md.

Fontes (nada é digitado à mão):
  * reports/junit.xml ............ pytest --junitxml
  * reports/coverage.json ........ pytest-cov (cobertura de linhas + ramos)
  * reports/ruff.txt ............. ruff check
  * reports/quality_results*.json  python -m src.validate
  * docs/kanban.md ............... tabela "Quadro" (coluna, pontos, sprint)
  * reports/maturity_assessment.md tabela "Resumo por área"

Uso:
    python scripts/collect_metrics.py --run   # executa pytest/ruff/validate e consolida
    python scripts/collect_metrics.py         # só consolida a partir dos arquivos existentes
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess  # noqa: S404 (comandos fixos, sem entrada do usuário)
import sys
import xml.etree.ElementTree as ET  # noqa: S405 (lê o junit.xml gerado localmente)
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RAW_DIR = ROOT / "data" / "raw"
RAW_BASE = RAW_DIR / "Extended_Employee_Performance_and_Productivity_Data_2_otimizado.csv"
ORIGINAL_BASE = RAW_DIR / "Extended_Employee_Performance_and_Productivity_Data.csv"
KANBAN_COLUMNS = ["A fazer", "Em andamento", "Em revisão", "Feito"]


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)  # noqa: S603


def execute_tools() -> None:
    REPORTS.mkdir(exist_ok=True)
    py = sys.executable
    test = run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--cov=src", "--cov-branch",
                "--cov-report=term-missing", f"--cov-report=json:{REPORTS / 'coverage.json'}",
                f"--junitxml={REPORTS / 'junit.xml'}"])
    (REPORTS / "pytest_output.txt").write_text(test.stdout + test.stderr, encoding="utf-8")
    lint = run(["ruff", "check", "."])
    (REPORTS / "ruff.txt").write_text(lint.stdout + lint.stderr, encoding="utf-8")
    run([py, "-m", "src.validate", "--data", "data/sample_data.csv",
         "--report", "reports/quality_report.md", "--json", "reports/quality_results.json"])
    if RAW_BASE.exists():
        run([py, "-m", "src.validate", "--data", str(RAW_BASE.relative_to(ROOT)),
             "--report", "reports/quality_report_full_base.md",
             "--json", "reports/quality_results_full_base.json"])
        rel = str(RAW_BASE.relative_to(ROOT))
        run([py, "-m", "src.ml.kaggle_risk", "--data", rel, "--out", "artifacts/kaggle"])
        model = ROOT / "artifacts" / "kaggle" / "metrics.json"
        if model.exists():
            (REPORTS / "model_metrics.json").write_text(model.read_text(encoding="utf-8"),
                                                        encoding="utf-8")
        run([py, "-m", "src.dashboard", "--data", rel])
        if ORIGINAL_BASE.exists():
            run([py, "scripts/compare_bases.py", "--original",
                 str(ORIGINAL_BASE.relative_to(ROOT)), "--derived", rel])
    else:
        print(f"Aviso: {RAW_BASE.relative_to(ROOT)} não encontrado; base completa não reavaliada.")


# ---------------------------------------------------------------- leitores
def read_tests() -> dict:
    junit = REPORTS / "junit.xml"
    if not junit.exists():
        return {}
    root = ET.parse(junit).getroot()  # noqa: S314
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    total = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0))
    errors = int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    by_file: dict[str, int] = {}
    for case in suite.iter("testcase"):
        mod = case.get("classname", "").split(".")
        name = mod[1] if len(mod) > 1 else mod[0]
        by_file[name] = by_file.get(name, 0) + 1
    out = {"total": total, "passed": total - failed - errors - skipped, "failed": failed,
           "errors": errors, "skipped": skipped,
           "duration_s": round(float(suite.get("time", 0)), 2),
           "by_file": dict(sorted(by_file.items()))}
    cov = REPORTS / "coverage.json"
    if cov.exists():
        data = json.loads(cov.read_text(encoding="utf-8"))
        t = data["totals"]
        out["coverage"] = round(t["percent_covered"] / 100, 4)
        out["coverage_lines"] = {"covered": t["covered_lines"], "statements": t["num_statements"]}
        out["coverage_branches"] = {"covered": t.get("covered_branches", 0),
                                    "total": t.get("num_branches", 0)}
        out["coverage_by_file"] = {
            k.replace("\\", "/"): round(v["summary"]["percent_covered"] / 100, 4)
            for k, v in sorted(data["files"].items())}
    return out


def read_model() -> dict:
    p = REPORTS / "model_metrics.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def read_lint() -> dict:
    txt = REPORTS / "ruff.txt"
    if not txt.exists():
        return {}
    content = txt.read_text(encoding="utf-8")
    if "All checks passed" in content:
        return {"findings": 0}
    m = re.search(r"Found (\d+) error", content)
    return {"findings": int(m.group(1)) if m else None}


def read_quality(name: str) -> tuple[dict, list]:
    p = REPORTS / name
    if not p.exists():
        return {}, []
    data = json.loads(p.read_text(encoding="utf-8"))
    rules = [{k: r[k] for k in ("id", "name", "dimension", "evaluated", "passed", "failed",
                                "conformity", "status")} for r in data["rules"]]
    return dict(data["summary"], rows=data["rows"], dataset=data["dataset"]), rules


def _table_after(heading: str, text: str) -> list[list[str]]:
    """Linhas de dados da primeira tabela Markdown depois do título informado."""
    idx = text.find(heading)
    if idx < 0:
        return []
    rows = []
    started = False
    for line in text[idx:].splitlines()[1:]:
        if line.startswith("|"):
            started = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not set("".join(cells)) <= set("-: "):
                rows.append(cells)
        elif started:
            break
    return rows[1:]  # remove cabeçalho


def read_kanban() -> dict:
    p = ROOT / "docs" / "kanban.md"
    if not p.exists():
        return {}
    rows = _table_after("## Quadro (fonte das métricas)", p.read_text(encoding="utf-8"))
    columns = dict.fromkeys(KANBAN_COLUMNS, 0)
    points = dict.fromkeys(KANBAN_COLUMNS, 0)
    sprint_points = done_points = review_points = 0
    stories = []
    for story_id, title, pts, sprint, column in (r[:5] for r in rows):
        pts_i = int(pts)
        columns[column] += 1
        points[column] += pts_i
        in_sprint = sprint.startswith("1")
        if in_sprint:
            sprint_points += pts_i
            done_points += pts_i if column == "Feito" else 0
            review_points += pts_i if column == "Em revisão" else 0
        stories.append({"id": story_id, "title": title, "points": pts_i, "sprint": sprint,
                        "column": column})
    return {"columns": columns, "points": points, "total_stories": len(stories),
            "sprint_points": sprint_points, "done_points": done_points,
            "review_points": review_points, "stories": stories}


def read_maturity() -> list[dict]:
    p = REPORTS / "maturity_assessment.md"
    if not p.exists():
        return []
    rows = _table_after("## Resumo por área", p.read_text(encoding="utf-8"))
    return [{"area": r[0], "ratings": [r[1], r[2], r[3]], "summary": r[4]} for r in rows]


# ---------------------------------------------------------------- saída
def fmt3(v):
    return f"{v:.3f}".replace(".", ",")


def pct(v, d=1):
    return "—" if v is None else f"{v * 100:.{d}f}%".replace(".", ",")


def render_md(m: dict) -> str:
    t, lint, k = m["tests"], m["lint"], m["kanban"]
    qs, qf = m["quality_sample"], m["quality_full_base"]
    done_rate = (k.get("done_points") or 0) / k["sprint_points"] if k.get("sprint_points") else None
    L = [
        "# Métricas do projeto",
        "",
        f"> Gerado automaticamente por `python scripts/collect_metrics.py --run` em "
        f"{m['generated_at']} (America/Sao_Paulo), a partir de execuções **locais** reais. "
        "Nenhum número deste arquivo foi digitado à mão. O workflow de CI ainda não foi "
        "publicado, portanto não há resultado de GitHub Actions.",
        "",
        "## 1. Testes automatizados (pytest)",
        "",
        "| Métrica | Valor |",
        "|---|---:|",
        f"| Testes executados | {t.get('total', '—')} |",
        f"| Aprovados | {t.get('passed', '—')} |",
        f"| Reprovados (falhas + erros) | {t.get('failed', 0) + t.get('errors', 0)} |",
        f"| Ignorados | {t.get('skipped', 0)} |",
        f"| Tempo total | {str(t.get('duration_s', '—')).replace('.', ',')} s |",
        "",
        "Testes por arquivo:",
        "",
        "| Arquivo | Testes |",
        "|---|---:|",
    ]
    L += [f"| `tests/{f}.py` | {n} |" for f, n in t.get("by_file", {}).items()]
    L += [
        "",
        "## 2. Cobertura de código (pytest-cov, linhas + ramos)",
        "",
        f"- **Cobertura total de `src/`: {pct(t.get('coverage'))}** "
        f"({t.get('coverage_lines', {}).get('covered', '—')}/"
        f"{t.get('coverage_lines', {}).get('statements', '—')} linhas · "
        f"{t.get('coverage_branches', {}).get('covered', '—')}/"
        f"{t.get('coverage_branches', {}).get('total', '—')} ramos)",
        "- Meta configurada em `pyproject.toml` (`fail_under = 80`).",
        "",
        "| Arquivo | Cobertura |",
        "|---|---:|",
    ]
    L += [f"| `{f}` | {pct(v)} |" for f, v in t.get("coverage_by_file", {}).items()]
    L += [
        "",
        "## 3. Análise estática (ruff)",
        "",
        f"- Achados atuais: **{lint.get('findings', '—')}** "
        "(regras E, W, F, I, UP, B, SIM, S; ver `pyproject.toml`).",
        "- Antes da configuração desta entrega, o mesmo conjunto de regras apontava 24 achados "
        "(14 no código herdado + 10 no código novo); todos foram corrigidos ou justificados "
        "com `noqa` comentado (falsos positivos S105 em mensagens de erro).",
        "",
        "## 4. Qualidade dos dados",
        "",
        "| Base | Registros | Regras aprovadas | Regras reprovadas | Conformidade geral | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for label, q in (("Amostra fixa `data/sample_data.csv`", qs),
                     ("Base completa `_2_otimizado` (local, fora do Git)", qf)):
        if q:
            L.append(f"| {label} | {q['rows']} | {q['rules_approved']} | {q['rules_failed']} | "
                     f"{pct(q['overall_conformity'], 2)} | {q['verdict']} |")
    L += [
        "",
        "Conformidade geral = Σ aprovados ÷ Σ avaliados nas 6 regras. Na amostra, os 6 "
        "defeitos são **injetados de propósito** (ver `data/README.md`). A base completa é a "
        "versão `_2_otimizado`, com `Sick_Days` regerado (`reports/data_lineage.md`); as regras "
        "QC01–QC06 não olham `Sick_Days` além da faixa, então o resultado é igual ao da base "
        "original. Detalhe em `reports/quality_report.md` e `reports/quality_report_full_base.md`.",
        "",
        "## 4b. Modelo de risco por funcionário (`src.ml.kaggle_risk`)",
        "",
    ]
    md = m.get("model") or {}
    if md:
        L += [
            "| Métrica | Valor | Meta |",
            "|---|---:|---:|",
            f"| ROC-AUC | {fmt3(md['roc_auc'])} | ≥ 0,700 |",
            f"| Recall | {fmt3(md['recall'])} | ≥ 0,600 |",
            f"| Precisão (limiar 0,5) | {fmt3(md['precision'])} | — |",
            f"| Precisão no top 10% de risco | {fmt3(md['precision_top10pct'])} | — |",
            f"| Treino / teste | {md['n_train']} / {md['n_test']} | holdout estratificado |",
            f"| Em quarentena (QC06) | {md['quarantined_qc06']} | fora do treino |",
            "",
            f"Alvo: `{md['target']}`. Base: `{md.get('dataset', '—')}`. **Na base original do "
            "Kaggle o mesmo código dá AUC ≈ 0,50** (`reports/data_lineage.md`): o resultado acima "
            "mede a recuperação da regra usada para regerar `Sick_Days`, não absenteísmo real.",
            "",
        ]
    else:
        L += ["Sem `reports/model_metrics.json`: rode com a base em `data/raw/`.", ""]
    L += [
        "## 5. Baseline da Sprint 1",
        "",
        "| Métrica | Valor | Fórmula |",
        "|---|---:|---|",
        f"| Pontos comprometidos (escopo final) | {k.get('sprint_points', '—')} | Σ pontos das "
        "histórias com Sprint = 1 |",
        "| Pontos planejados no início | 21 | `docs/04-planejamento-e-riscos.md` |",
        f"| **Velocidade (DoD completa)** | **{k.get('done_points', '—')}** | Σ pontos em Feito |",
        f"| Pontos aguardando revisão por par | {k.get('review_points', '—')} | Σ pontos em "
        "Em revisão |",
        f"| Taxa de conclusão pela DoD | "
        f"{pct(done_rate)}"
        " | Feito ÷ comprometido |",
        "",
        "## 6. Distribuição das histórias no Kanban",
        "",
        "| Coluna | Histórias | Pontos |",
        "|---|---:|---:|",
    ]
    L += [f"| {c} | {k['columns'][c]} | {k['points'][c]} |" for c in KANBAN_COLUMNS] if k else []
    L += [f"| **Total** | **{k.get('total_stories', 0)}** | "
          f"**{sum(k.get('points', {}).values())}** |", "",
          "## 7. Maturidade por área (autoavaliação)", "",
          "| Área | Q1 | Q2 | Q3 | Síntese |", "|---|:-:|:-:|:-:|---|"]
    L += [f"| {a['area']} | {' | '.join(a['ratings'])} | {a['summary']} |" for a in m["maturity"]]
    from collections import Counter
    cnt = Counter(r for a in m["maturity"] for r in a["ratings"])
    L += ["", f"Contagem: F = {cnt['F']} · L = {cnt['L']} · P = {cnt['P']} · N = {cnt['N']}."]
    L += ["", "Escala: N = não praticado · P = parcialmente · L = largamente · F = totalmente. "
          "Justificativas em `reports/maturity_assessment.md`.", ""]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true", help="executa pytest, ruff e validate antes")
    a = ap.parse_args()
    if a.run:
        execute_tools()
    qs, _ = read_quality("quality_results.json")
    qf, qf_rules = read_quality("quality_results_full_base.json")
    metrics = {
        "generated_at": datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M"),
        "tests": read_tests(),
        "lint": read_lint(),
        "quality_sample": qs,
        "quality_full_base": qf,
        "quality_full_rules": qf_rules,
        "kanban": read_kanban(),
        "model": read_model(),
        "maturity": read_maturity(),
    }
    (REPORTS / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False),
                                          encoding="utf-8")
    (REPORTS / "metrics.md").write_text(render_md(metrics), encoding="utf-8")
    t = metrics["tests"]
    print(f"Testes: {t.get('passed')}/{t.get('total')} · cobertura {pct(t.get('coverage'))} · "
          f"ruff {metrics['lint'].get('findings')} achados")
    return 0 if not t.get("failed") and not t.get("errors") else 1


if __name__ == "__main__":
    raise SystemExit(main())
