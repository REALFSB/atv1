"""Aplicação web do DataTrack (Flask): login, cadastro, dashboard e painéis protegidos.

Executar localmente:
    flask --app src.webapp init-db
    flask --app src.webapp create-user          # ou use a tela /cadastro
    flask --app src.webapp run --debug
"""
from __future__ import annotations

import os
import secrets
import warnings
from datetime import timedelta
from pathlib import Path

import click
from flask import Flask, render_template, request

from . import auth, db, views
from .security import LoginRateLimiter, apply_security_headers, csrf_token, verify_csrf

ROOT = Path(__file__).resolve().parents[2]


def _env_flag(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "sim"}


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_path=str(ROOT / "instance"))

    secret = os.environ.get("DATATRACK_SECRET_KEY")
    if not secret and not (test_config or {}).get("SECRET_KEY"):
        warnings.warn("DATATRACK_SECRET_KEY não definida: usando chave aleatória; as sessões "
                      "serão perdidas a cada reinício.", stacklevel=2)
        secret = secrets.token_hex(32)

    app.config.from_mapping(
        SECRET_KEY=secret,
        DATABASE=os.environ.get("DATATRACK_DB", str(Path(app.instance_path) / "users.db")),
        REPORTS_DIR=str(ROOT / "reports"),
        PANELS_DIR=str(ROOT / "paineis"),
        ALLOW_SIGNUP=_env_flag("DATATRACK_ALLOW_SIGNUP", True),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=_env_flag("DATATRACK_SECURE_COOKIE", False),  # True atrás de HTTPS
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        LOGIN_MAX_FAILURES=5,
        LOGIN_WINDOW_SECONDS=900,
    )
    if test_config:
        app.config.update(test_config)

    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    app.extensions["login_limiter"] = LoginRateLimiter(app.config["LOGIN_MAX_FAILURES"],
                                                       app.config["LOGIN_WINDOW_SECONDS"])

    app.teardown_appcontext(db.close_db)
    app.before_request(verify_csrf)
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.after_request
    def _headers(response):
        is_panel = request.path.startswith("/paineis/")
        if request.endpoint not in (None, "static"):
            response.headers["Cache-Control"] = "no-store"  # páginas privadas fora do cache
        return apply_security_headers(response, is_legacy_panel=is_panel)

    @app.errorhandler(400)
    def _bad_request(err):
        return render_template("error.html", code=400, message=err.description), 400

    @app.errorhandler(404)
    def _not_found(_err):
        return render_template("error.html", code=404, message="Página não encontrada."), 404

    app.register_blueprint(auth.bp)
    app.register_blueprint(views.bp)

    with app.app_context():
        db.init_db()

    @app.cli.command("init-db")
    def init_db_command():
        """Cria a tabela de usuários (idempotente)."""
        db.init_db()
        click.echo(f"Banco pronto em {app.config['DATABASE']}")

    @app.cli.command("create-user")
    @click.option("--name", prompt="Nome")
    @click.option("--email", prompt="E-mail")
    @click.password_option("--password", prompt="Senha")
    def create_user_command(name, email, password):
        """Cadastra um usuário pela linha de comando."""
        problems = auth.password_problems(password)
        if problems:
            raise click.ClickException(" ".join(problems))
        try:
            user = db.create_user(name, email, password)
        except db.UserExistsError as exc:
            raise click.ClickException("Já existe uma conta com este e-mail.") from exc
        click.echo(f"Usuário {user.email} criado (id {user.id}).")

    return app
