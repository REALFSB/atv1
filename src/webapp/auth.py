"""Autenticação: login, cadastro, logout e proteção de rotas (US12)."""
from __future__ import annotations

import functools
import re

from flask import (
    Blueprint,
    current_app,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .db import UserExistsError, authenticate, create_user, get_user, normalize_email
from .security import safe_next

bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD = 8
INVALID_CREDENTIALS = "E-mail ou senha inválidos."


def password_problems(password: str) -> list[str]:
    problems = []
    if len(password) < MIN_PASSWORD:
        problems.append(f"A senha precisa ter pelo menos {MIN_PASSWORD} caracteres.")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        problems.append("A senha precisa combinar letras e números.")
    return problems


def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("user") is None:
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)
    return wrapped


@bp.before_app_request
def load_logged_in_user() -> None:
    user_id = session.get("user_id")
    g.user = get_user(user_id) if user_id is not None else None
    if user_id is not None and g.user is None:  # usuário removido com sessão aberta
        session.clear()


def _start_session(user) -> None:
    token = session.get("csrf_token")
    session.clear()  # evita fixação de sessão: nada da sessão anônima é reaproveitado
    session.permanent = True
    session["user_id"] = user.id
    if token:
        session["csrf_token"] = token


@bp.route("/login", methods=["GET", "POST"])
def login():
    next_url = safe_next(request.values.get("next"), url_for("views.dashboard"))
    if g.user is not None:
        return redirect(next_url)

    errors: dict[str, str] = {}
    email = ""
    status = 200
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        if not email:
            errors["email"] = "Informe o e-mail."
        elif not EMAIL_RE.match(email):
            errors["email"] = "Informe um e-mail válido."
        if not password:
            errors["password"] = "Informe a senha."  # noqa: S105 (mensagem de erro)

        if errors:
            status = 400
        else:
            limiter = current_app.extensions["login_limiter"]
            key = f"{request.remote_addr}|{normalize_email(email)}"
            wait = limiter.retry_after(key)
            if wait:
                minutes = max(1, round(wait / 60))
                errors["form"] = (f"Muitas tentativas sem sucesso. Tente de novo em "
                                  f"{minutes} min.")
                status = 429
            else:
                user = authenticate(email, password)
                if user is None:
                    limiter.record_failure(key)
                    errors["form"] = INVALID_CREDENTIALS
                    status = 401
                else:
                    limiter.reset(key)
                    _start_session(user)
                    return redirect(next_url)

    return render_template("login.html", errors=errors, email=email,
                           next_url=request.values.get("next", ""),
                           allow_signup=current_app.config["ALLOW_SIGNUP"]), status


@bp.route("/cadastro", methods=["GET", "POST"])
def register():
    if not current_app.config["ALLOW_SIGNUP"]:
        return redirect(url_for("auth.login"))
    if g.user is not None:
        return redirect(url_for("views.dashboard"))

    errors: dict[str, str] = {}
    form = {"name": "", "email": ""}
    status = 200
    if request.method == "POST":
        form = {"name": request.form.get("name", "").strip(),
                "email": request.form.get("email", "").strip()}
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not form["name"]:
            errors["name"] = "Informe seu nome."
        if not form["email"]:
            errors["email"] = "Informe o e-mail."
        elif not EMAIL_RE.match(form["email"]):
            errors["email"] = "Informe um e-mail válido."
        if not password:
            errors["password"] = "Crie uma senha."  # noqa: S105 (mensagem de erro)
        elif problems := password_problems(password):
            errors["password"] = " ".join(problems)
        if password and password != confirm:
            errors["confirm"] = "As senhas não conferem."
        if not errors:
            try:
                user = create_user(form["name"], form["email"], password)
            except UserExistsError:
                errors["email"] = "Já existe uma conta com este e-mail."
            else:
                _start_session(user)
                return redirect(url_for("views.dashboard"))
        status = 400
    return render_template("register.html", errors=errors, form=form,
                           min_password=MIN_PASSWORD), status


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login", saiu=1))
