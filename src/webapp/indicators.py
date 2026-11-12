"""Indicadores do dashboard. Lê apenas arquivos gerados pelas execuções reais
(reports/metrics.json, criado por scripts/collect_metrics.py). Se o arquivo não
existir, o dashboard mostra "—" em vez de inventar números."""
from __future__ import annotations

import json
from pathlib import Path


def load_metrics(reports_dir: Path) -> dict | None:
    path = Path(reports_dir) / "metrics.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def pct(value: float | None, digits: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.{digits}f}%".replace(".", ",")


def build_cards(metrics: dict | None) -> list[dict]:
    """Cartões principais. Cada um diz de onde veio o número."""
    if not metrics:
        return []
    t, q, qf, k, md = (metrics.get(x) or {} for x in ("tests", "quality_sample",
                                                       "quality_full_base", "kanban", "model"))
    cards = [
        {"label": "Testes automatizados",
         "value": f"{t.get('passed', '—')}/{t.get('total', '—')}",
         "hint": f"{t.get('failed', 0)} falhas · {t.get('skipped', 0)} ignorados",
         "tone": "ok" if t and not t.get("failed") else "warn", "source": "pytest"},
        {"label": "Cobertura de código", "value": pct(t.get("coverage")),
         "hint": "linhas + ramos de src/",
         "tone": "ok" if (t.get("coverage") or 0) >= .8 else "warn",
         "source": "pytest-cov"},
        {"label": "Conformidade · base Kaggle", "value": pct(qf.get("overall_conformity"), 2),
         "hint": f"{qf.get('rules_approved', '—')} de {qf.get('rules_total', '—')} regras · "
                 f"{qf.get('verdict', '—')}",
         "tone": "ok" if qf.get("verdict") == "LIBERADA" else "warn", "source": "src/validate.py"},
        {"label": "Conformidade · amostra fixa", "value": pct(q.get("overall_conformity"), 2),
         "hint": f"{q.get('rules_failed', '—')} regras reprovadas (defeitos injetados)",
         "tone": "neutral", "source": "data/sample_data.csv"},
        {"label": "Baseline Sprint 1",
         "value": f"{k.get('done_points', 0)}/{k.get('sprint_points', '—')} pts",
         "hint": "pontos em Feito ÷ pontos comprometidos",
         "tone": "warn" if k.get("done_points", 0) < (k.get("sprint_points") or 0) else "ok",
         "source": "docs/kanban.md"},
    ]
    if md:
        cards.append({
            "label": "Modelo · base semi-sintética",
            "value": f"AUC {md['roc_auc']:.2f}".replace(".", ","),
            "hint": f"recall {md['recall']:.2f} · na base original: AUC ≈ 0,50".replace(".", ","),
            "tone": "warn", "source": "src/ml/kaggle_risk.py"})
    return cards
