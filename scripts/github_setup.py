"""Monta a gestão de configuração no GitHub: issues, quadro, main protegida,
histórico por branches e um pull request por história.

O script NÃO aprova nem faz merge de nada: a revisão por um colega é humana.
Fluxo (rode na raiz de uma CÓPIA do projeto, num repositório GitHub novo e vazio):

    gh auth login                         # uma vez; para o quadro: gh auth refresh -s project
    python scripts/github_setup.py init --repo SEU_USUARIO/datatrack
    python scripts/github_setup.py pr ingestao   # abre o PR; um colega revisa e faz o merge
    python scripts/github_setup.py pr modelo     # só depois do merge do anterior
    ...                                          # ordem em `python scripts/github_setup.py plan`
    python scripts/github_setup.py trace         # gera docs/rastreabilidade.md com links reais

`--dry-run` executa só a parte local (git) e imprime os comandos `gh`, sem tocar no GitHub.
"""
from __future__ import annotations

import argparse
import csv
import json
import shlex
import subprocess  # noqa: S404 (comandos fixos de git/gh)
import sys
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".github-setup.json"   # números de issues e PRs criados (fica fora do Git)

BASE_FILES = [
    "README.md", "index.html", "pyproject.toml", "requirements.txt", ".gitignore",
    ".github/**", "docs/01-backlog.md", "docs/02-requisitos.md", "docs/03-arquitetura.md",
    "docs/04-planejamento-e-riscos.md", "docs/backlog.md", "docs/backlog_issues.csv",
    "paineis/*.html", "paineis/datatrack.js", "data/.gitkeep", "data/README.md",
    "src/__init__.py", "src/data/__init__.py", "src/ml/__init__.py",
    "src/serving/__init__.py", "tests/conftest.py", "tests/test_repo.py",
]

# Ordem de dependência: cada PR só passa no CI se os anteriores já estiverem na main.
STEPS: dict[str, dict] = {
    "ingestao": {
        "branch": "feature/US3-US4-ingestao-lgpd", "stories": ["US3", "US4"],
        "title": "feat(data): ingestão com validação de nulos e pseudonimização (US3, US4)",
        "files": ["src/data/ingest.py", "src/ingest.py", "tests/test_ingest.py"],
        "tests": "tests/test_ingest.py",
    },
    "modelo": {
        "branch": "feature/US2-modelo-operacional", "stories": ["US2"],
        "title": "feat(ml): atributos e treino com split temporal (US2)",
        "files": ["src/ml/features.py", "src/ml/train.py", "src/features.py", "src/train.py",
                  "tests/test_features.py", "tests/test_train.py"],
        "tests": "tests/test_features.py, tests/test_train.py",
    },
    "ranking": {
        "branch": "feature/US1-US5-US6-ranking", "stories": ["US1", "US5", "US6"],
        "title": "feat(serving): ranking de risco, exportação CSV e fatores (US1, US5, US6)",
        "files": ["src/serving/risk.py", "src/serve.py", "tests/test_serve.py"],
        "tests": "tests/test_serve.py",
    },
    "qualidade": {
        "branch": "feature/US11-qualidade-dados", "stories": ["US11"],
        "title": "feat(validate): 6 regras de qualidade em pandas e SQL com relatório (US11)",
        "files": ["src/validate.py", "sql/**", "data/sample_data.csv", "scripts/build_sample.py",
                  "tests/test_validate.py", "tests/test_smoke.py",
                  "reports/quality_report*.md", "reports/quality_results*.json", "reports/sbar.md"],
        "tests": "tests/test_validate.py, tests/test_smoke.py",
    },
    "autenticacao": {
        "branch": "feature/US12-autenticacao", "stories": ["US12"],
        "title": "feat(webapp): login, cadastro, logout e rotas protegidas (US12)",
        "files": ["src/webapp/**", "tests/test_auth.py"],
        "tests": "tests/test_auth.py",
    },
    "modelo-funcionarios": {
        "branch": "feature/US2-modelo-por-funcionario", "stories": ["US2", "US8"],
        "title": "feat(ml): modelo por funcionário na base Kaggle e gerador do painel (US2, US8)",
        "files": ["src/data/employees.py", "src/ml/kaggle_risk.py", "src/dashboard.py",
                  "data/dashboard_sources_snapshot.json", "scripts/compare_bases.py",
                  "paineis/risco-data.js", "paineis/dashboard-data.js",
                  "tests/test_employee_model.py", "reports/data_lineage.md",
                  "docs/05-dados-reais.md"],
        "tests": "tests/test_employee_model.py",
    },
    "gestao": {
        "branch": "docs/sprint-1-gestao", "stories": [],
        "title": "docs: Sprint 1, autoavaliação, plano de melhoria e métricas",
        "files": ["docs/**", "reports/**", "scripts/**", "apresentacao/**"],
        "tests": "—",
    },
}


# ---------------------------------------------------------------- utilidades
class Runner:
    def __init__(self, dry: bool):
        self.dry = dry

    def git(self, *args: str, check: bool = True) -> str:
        res = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)  # noqa: S603,S607
        if check and res.returncode:
            sys.exit(f"git {' '.join(args)} falhou:\n{res.stderr}")
        return res.stdout.strip()

    def gh(self, *args: str) -> str:
        cmd = ["gh", *args]
        if self.dry:
            print("[dry-run]", shlex.join(cmd))
            return ""
        res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)  # noqa: S603,S607
        if res.returncode:
            sys.exit(f"{shlex.join(cmd)} falhou:\n{res.stderr}")
        return res.stdout.strip()


def load_state() -> dict:
    return json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {"issues": {}}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def tracked_files() -> list[str]:
    """Arquivos do projeto respeitando o .gitignore (o que o git adicionaria)."""
    res = subprocess.run(["git", "ls-files", "--others", "--cached", "--exclude-standard"],  # noqa: S603,S607
                         cwd=ROOT, capture_output=True, text=True, check=True)
    return [f for f in res.stdout.splitlines() if f]


def match(files: list[str], patterns: list[str]) -> list[str]:
    return sorted(f for f in files if any(fnmatch(f, p) for p in patterns))


def claimed_by_earlier(step: str) -> list[str]:
    files = tracked_files()
    out = match(files, BASE_FILES)
    for name, spec in STEPS.items():
        if name == step:
            break
        out += match(files, spec["files"])
    return out


# ---------------------------------------------------------------- comandos
def cmd_plan(_a, _r) -> None:
    print("Ordem dos PRs (cada um depende do merge do anterior):")
    for i, (name, spec) in enumerate(STEPS.items(), 1):
        print(f"{i}. {name:20} {spec['branch']:40} {', '.join(spec['stories']) or '—'}")


def cmd_init(a, r: Runner) -> None:
    state = load_state()
    state["repo"] = a.repo
    if not (ROOT / ".git").exists():
        r.git("init", "-b", "main")
    if r.git("rev-parse", "--verify", "main", check=False):
        print("main já existe: pulando commit base.")
    else:
        files = match(tracked_files(), BASE_FILES)
        r.git("add", "--", *files)
        r.git("commit", "-m", "chore: estrutura do projeto, planejamento e CI\n\n"
              "Base para o histórico por branches da Sprint 1.")
    # labels e issues
    labels = {"user-story": "1d76db", "onda-1": "0e8a16", "onda-2": "fbca04",
              "sprint-1": "5319e7", "dados": "c5def5", "segurança": "b60205"}
    for name, color in labels.items():
        r.gh("label", "create", name, "--color", color, "--force", "--repo", a.repo)
    with (ROOT / "docs" / "backlog_issues.csv").open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            sid = row["title"].split(":")[0]
            if sid in state["issues"]:
                continue
            onda = "onda-1" if "onda-1" in row["labels"] else "onda-2"
            extra = ["--label", "sprint-1"] if onda == "onda-1" else []
            url = r.gh("issue", "create", "--repo", a.repo, "--title", row["title"],
                       "--body", row["body"] + "\n\nDetalhes: docs/backlog.md",
                       "--label", "user-story", "--label", onda, *extra)
            state["issues"][sid] = url.rsplit("/", 1)[-1] if url else f"<{sid}>"
    save_state(state)
    # remoto, push e proteção da main
    if not r.dry:
        if not r.git("remote", check=False):
            r.git("remote", "add", "origin", f"https://github.com/{a.repo}.git")
        r.git("push", "-u", "origin", "main")
    protection = {
        "required_status_checks": {"strict": True, "contexts": [
            "ruff", "pytest (Python 3.11)", "pytest (Python 3.12)"]},
        "enforce_admins": True,
        "required_pull_request_reviews": {"required_approving_review_count": 1,
                                          "dismiss_stale_reviews": True},
        "restrictions": None,
        "allow_force_pushes": False, "allow_deletions": False,
        "required_conversation_resolution": True,
    }
    payload = ROOT / ".github-protection.json"
    payload.write_text(json.dumps(protection), encoding="utf-8")
    r.gh("api", "-X", "PUT", f"repos/{a.repo}/branches/main/protection",
         "--input", str(payload))
    if a.project:
        owner = a.repo.split("/")[0]
        r.gh("project", "create", "--owner", owner, "--title", "DataTrack · Sprint 1")
        print("Quadro criado. Adicione as issues: gh project item-add <N> --owner "
              f"{owner} --url <url-da-issue> (ou pela interface, Status = coluna do Kanban).")
    print("init concluído. Próximo: python scripts/github_setup.py pr ingestao")


def cmd_pr(a, r: Runner) -> None:
    state = load_state()
    spec = STEPS[a.step]
    r.git("checkout", "main")
    if not r.dry:
        r.git("pull", "--ff-only", "origin", "main")
    before = set(claimed_by_earlier(a.step))
    files = [f for f in match(tracked_files(), spec["files"]) if f not in before]
    if not files:
        sys.exit(f"Nada a commitar para '{a.step}'.")
    r.git("checkout", "-B", spec["branch"])
    r.git("add", "--", *files)
    closes = [f"Closes #{state['issues'].get(s, '?')}" for s in spec["stories"]]
    r.git("commit", "-m", spec["title"] + "\n\n" + "\n".join(closes or ["Sem história associada"]))
    body = "\n".join([
        f"**Histórias:** {', '.join(spec['stories']) or '—'}",
        *closes, "",
        f"**Testes que comprovam os critérios de aceite:** `{spec['tests']}`",
        "", "**Checklist (DoD)**", "- [ ] critérios de aceite cobertos por teste",
        "- [ ] `pytest` verde no CI", "- [ ] cobertura ≥ 80%", "- [ ] `ruff check .` sem alertas",
        "- [ ] revisado e aprovado por um colega (comentários respondidos no PR)",
    ])
    if not r.dry:
        r.git("push", "-u", "origin", spec["branch"])
    url = r.gh("pr", "create", "--repo", state.get("repo", a.repo or ""), "--base", "main",
               "--head", spec["branch"], "--title", spec["title"], "--body", body)
    state.setdefault("prs", {})[a.step] = url or f"<pr {spec['branch']}>"
    save_state(state)
    print(f"PR aberto: {url or '(dry-run)'}\nPeça a revisão a um colega. Merge só após "
          "aprovação + CI verde; depois rode o próximo passo.")
    if r.dry:
        r.git("checkout", "main")
        r.git("merge", "--no-ff", spec["branch"], "-m", f"Merge {spec['branch']} (dry-run local)")


def cmd_trace(a, r: Runner) -> None:
    state = load_state()
    repo = state.get("repo", a.repo)
    rows = []
    for name, spec in STEPS.items():
        for sid in spec["stories"] or ["—"]:
            issue = state["issues"].get(sid, "—")
            pr = state.get("prs", {}).get(name, "—")
            review = "—"
            if not r.dry and pr.startswith("http"):
                info = json.loads(r.gh("pr", "view", pr, "--repo", repo, "--json",
                                       "state,reviewDecision,mergedAt"))
                review = f"{info['state']} · {info.get('reviewDecision') or 'sem revisão'}"
            link = f"[#{issue}](https://github.com/{repo}/issues/{issue})" if issue.isdigit() \
                else issue
            rows.append(f"| {sid} | {link} | `{spec['branch']}` | {pr} · {review} | "
                        f"`{spec['tests']}` |")
    out = ROOT / "docs" / "rastreabilidade.md"
    out.write_text("\n".join([
        "# Rastreabilidade: história → issue → branch → PR → teste", "",
        "> Gerado por `python scripts/github_setup.py trace` a partir do GitHub.", "",
        "| História | Issue | Branch | Pull request e revisão | Teste |",
        "|---|---|---|---|---|", *rows, ""]), encoding="utf-8")
    print("Gerado:", out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    p_init = sub.add_parser("init")
    p_init.add_argument("--repo", required=True, help="dono/repositório (já criado e vazio)")
    p_init.add_argument("--project", action="store_true", help="cria quadro no GitHub Projects")
    p_pr = sub.add_parser("pr")
    p_pr.add_argument("step", choices=list(STEPS))
    p_pr.add_argument("--repo")
    p_tr = sub.add_parser("trace")
    p_tr.add_argument("--repo")
    a = ap.parse_args(argv)
    r = Runner(a.dry_run)
    {"plan": cmd_plan, "init": cmd_init, "pr": cmd_pr, "trace": cmd_trace}[a.cmd](a, r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
