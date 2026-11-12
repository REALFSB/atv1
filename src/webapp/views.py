"""Páginas privadas: dashboard e painéis legados (servidos só para usuários autenticados)."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, abort, current_app, g, redirect, render_template, url_for
from markupsafe import escape
from werkzeug.utils import safe_join

from .auth import login_required
from .indicators import build_cards, load_metrics, pct
from .security import csrf_token

bp = Blueprint("views", __name__)

FEATURES = [
    {"title": "Dashboard Geral", "href": "paineis/index.html", "icon": "grid",
     "text": "Visão consolidada da operação, alertas e indicadores do dia."},
    {"title": "Equipes & Escalas", "href": "paineis/equipes.html", "icon": "users",
     "text": "Ranking de risco de ausência por operador, filtro por setor e exportação CSV."},
    {"title": "Gestão de Metas", "href": "paineis/metas.html", "icon": "target",
     "text": "Metas por célula e impacto esperado das ausências (Onda 2)."},
    {"title": "Relatórios", "href": "paineis/relatorios.html", "icon": "file",
     "text": "Relatórios semanais para as reuniões de operação."},
]



def greeting(now: datetime | None = None) -> str:
    now = now or datetime.now(ZoneInfo("America/Sao_Paulo"))
    if now.hour < 12:
        return "Bom dia"
    return "Boa tarde" if now.hour < 18 else "Boa noite"


@bp.route("/")
def index():
    return redirect(url_for("views.dashboard" if g.get("user") else "auth.login"))


@bp.route("/dashboard")
@login_required
def dashboard():
    metrics = load_metrics(current_app.config["REPORTS_DIR"])
    return render_template(
        "dashboard.html",
        greeting=greeting(),
        cards=build_cards(metrics),
        metrics=metrics,
        features=FEATURES,
        pct=pct,
    )


@bp.route("/paineis/<path:filename>")
@login_required
def legacy_panel(filename: str):
    """Serve os painéis HTML antigos atrás do login e liga o botão de sair deles ao logout."""
    panels_dir = Path(current_app.config["PANELS_DIR"])
    target = safe_join(str(panels_dir), filename)
    if target is None or not Path(target).is_file():
        abort(404)
    path = Path(target)
    if path.suffix != ".html":
        mimetype = "application/javascript" if path.suffix == ".js" else None
        return Response(path.read_bytes(), mimetype=mimetype or "application/octet-stream")

    html = path.read_text(encoding="utf-8")
    meta = f'<meta name="dt-user" content="{escape(g.user.name)}">'
    form = (f'<form id="dt-logout" method="post" action="{url_for("auth.logout")}" hidden>'
            f'<input type="hidden" name="csrf_token" value="{escape(csrf_token())}"></form>')
    html = html.replace("</head>", meta + "</head>", 1)
    # o formulário vem logo após <body> para existir quando o datatrack.js montar a barra lateral
    html = re.sub(r"(<body[^>]*>)", lambda m: m.group(1) + form, html, count=1)
    return Response(html, mimetype="text/html")
