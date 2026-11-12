"""Testes da autenticação (US12). Cobrem os seis cenários pedidos — credenciais válidas,
senha incorreta, campos vazios, usuário inexistente, páginas privadas e logout — e as
proteções de segurança (hash, CSRF, open redirect, força bruta)."""
import re
import sqlite3
from contextlib import closing

import pytest

from src.webapp import create_app
from src.webapp.db import create_user
from src.webapp.security import LoginRateLimiter, safe_next

pytestmark = pytest.mark.auth

EMAIL, PASSWORD, NAME = "ana@datatrack.dev", "Senha123forte", "Ana Souza"
CSRF_RE = re.compile(r'name="csrf_token" value="([^"]+)"')


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "test-secret",
                      "DATABASE": str(tmp_path / "users.db"),
                      "REPORTS_DIR": str(tmp_path / "reports")})
    with app.app_context():
        create_user(NAME, EMAIL, PASSWORD)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def csrf(client, path="/login") -> str:
    return CSRF_RE.search(client.get(path).get_data(as_text=True)).group(1)


def login(client, email=EMAIL, password=PASSWORD, **extra):
    data = {"email": email, "password": password, "csrf_token": csrf(client), **extra}
    return client.post("/login", data=data)


# ---------------------------------------------------------------- 1. credenciais válidas
def test_login_with_valid_credentials_redirects_to_dashboard(client):
    resp = login(client)
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/dashboard")
    page = client.get("/dashboard").get_data(as_text=True)
    assert "Ana." in page and "Sair" in page


def test_email_is_case_and_space_insensitive(client):
    assert login(client, email="  ANA@DataTrack.dev ").status_code == 302


# ---------------------------------------------------------------- 2. senha incorreta
def test_wrong_password_is_rejected_with_generic_message(client):
    resp = login(client, password="SenhaErrada9")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 401 and "E-mail ou senha inválidos." in body
    assert client.get("/dashboard").status_code == 302  # continua sem sessão


# ---------------------------------------------------------------- 3. campos vazios
@pytest.mark.parametrize(
    ("email", "password", "messages"),
    [
        ("", "", ["Informe o e-mail.", "Informe a senha."]),
        (EMAIL, "", ["Informe a senha."]),
        ("", PASSWORD, ["Informe o e-mail."]),
        ("   ", PASSWORD, ["Informe o e-mail."]),
        ("nao-e-email", PASSWORD, ["Informe um e-mail válido."]),
    ],
)
def test_empty_or_malformed_fields_return_400(client, email, password, messages):
    resp = login(client, email=email, password=password)
    body = resp.get_data(as_text=True)
    assert resp.status_code == 400
    for msg in messages:
        assert msg in body


# ---------------------------------------------------------------- 4. usuário inexistente
def test_unknown_user_gets_same_message_as_wrong_password(client):
    unknown = login(client, email="ninguem@datatrack.dev")
    wrong = login(client, password="SenhaErrada9")
    assert unknown.status_code == wrong.status_code == 401
    assert "E-mail ou senha inválidos." in unknown.get_data(as_text=True)


# ---------------------------------------------------------------- 5. páginas privadas
@pytest.mark.parametrize("path", ["/dashboard", "/paineis/index.html", "/paineis/equipes.html",
                                  "/paineis/risco-data.js"])
def test_private_pages_redirect_anonymous_user_to_login(client, path):
    resp = client.get(path)
    assert resp.status_code == 302
    assert "/login?next=" in resp.headers["Location"]


def test_after_login_user_returns_to_requested_page(client):
    resp = login(client, next="/paineis/equipes.html")
    assert resp.headers["Location"].endswith("/paineis/equipes.html")
    panel = client.get("/paineis/equipes.html")
    html = panel.get_data(as_text=True)
    assert panel.status_code == 200 and 'id="dt-logout"' in html
    assert f'<meta name="dt-user" content="{NAME}">' in html


@pytest.mark.parametrize("evil", ["https://evil.example/x", "//evil.example", "/\\evil.example",
                                  "javascript:alert(1)"])
def test_next_parameter_cannot_redirect_off_site(client, evil):
    resp = login(client, next=evil)
    assert resp.headers["Location"].endswith("/dashboard")


def test_panel_path_traversal_is_blocked(client):
    login(client)
    for path in ("/paineis/../pyproject.toml", "/paineis/..%2fpyproject.toml",
                 "/paineis/%2e%2e/%2e%2e/pyproject.toml"):
        assert client.get(path).status_code == 404


# ---------------------------------------------------------------- 6. logout
def test_logout_ends_session(client):
    login(client)
    token = csrf(client, "/dashboard")
    resp = client.post("/logout", data={"csrf_token": token})
    assert resp.status_code == 302 and "/login" in resp.headers["Location"]
    assert client.get("/dashboard").status_code == 302


def test_logout_requires_post_and_csrf(client):
    login(client)
    assert client.get("/logout").status_code == 405
    assert client.post("/logout", data={}).status_code == 400
    assert client.get("/dashboard").status_code == 200  # sessão intacta


# ---------------------------------------------------------------- segurança
def test_password_is_stored_only_as_hash(app):
    with closing(sqlite3.connect(app.config["DATABASE"])) as conn:
        stored = conn.execute("SELECT password_hash FROM users WHERE email = ?",
                              (EMAIL,)).fetchone()[0]
    assert PASSWORD not in stored and stored.startswith(("scrypt:", "pbkdf2:"))


def test_post_without_csrf_token_is_rejected(client):
    resp = client.post("/login", data={"email": EMAIL, "password": PASSWORD})
    assert resp.status_code == 400


def test_session_cookie_is_httponly_and_samesite(client):
    login(client)
    cookie = client.get_cookie("session")
    assert cookie is not None and cookie.http_only and cookie.same_site == "Lax"


def test_security_headers_on_app_pages(client):
    resp = client.get("/login")
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]
    assert resp.headers["Cache-Control"] == "no-store"


def test_brute_force_is_throttled_after_five_failures(client):
    for _ in range(5):
        assert login(client, password="SenhaErrada9").status_code == 401
    blocked = login(client)  # até a senha certa é barrada durante o bloqueio
    assert blocked.status_code == 429 and "Muitas tentativas" in blocked.get_data(as_text=True)


def test_rate_limiter_window_expires():
    lim = LoginRateLimiter(max_failures=2, window_seconds=10)
    lim.record_failure("k", now=0)
    lim.record_failure("k", now=1)
    assert lim.retry_after("k", now=2) > 0
    assert lim.retry_after("k", now=12) == 0


@pytest.mark.parametrize(("target", "expected"), [
    (None, "/d"), ("/paineis/x.html", "/paineis/x.html"), ("http://a.b/", "/d"), ("relativo", "/d"),
])
def test_safe_next(target, expected):
    assert safe_next(target, "/d") == expected


# ---------------------------------------------------------------- cadastro
def register(client, **fields):
    data = {"name": "Bruno Lima", "email": "bruno@datatrack.dev", "password": "Outra123senha",
            "confirm": "Outra123senha", "csrf_token": csrf(client, "/cadastro")}
    data.update(fields)
    return client.post("/cadastro", data=data)


def test_register_creates_account_and_logs_in(client):
    resp = register(client)
    assert resp.status_code == 302 and resp.headers["Location"].endswith("/dashboard")
    assert "Bruno." in client.get("/dashboard").get_data(as_text=True)


@pytest.mark.parametrize(("fields", "message"), [
    ({"email": EMAIL}, "Já existe uma conta com este e-mail."),
    ({"password": "curta1", "confirm": "curta1"}, "pelo menos 8 caracteres"),
    ({"password": "somenteletras", "confirm": "somenteletras"}, "letras e números"),
    ({"confirm": "diferente123"}, "As senhas não conferem."),
    ({"name": ""}, "Informe seu nome."),
])
def test_register_validation(client, fields, message):
    resp = register(client, **fields)
    assert resp.status_code == 400 and message in resp.get_data(as_text=True)


def test_signup_can_be_disabled(tmp_path):
    app = create_app({"TESTING": True, "SECRET_KEY": "x", "ALLOW_SIGNUP": False,
                      "DATABASE": str(tmp_path / "u.db")})
    c = app.test_client()
    assert c.get("/cadastro").status_code == 302
    assert "Criar conta" not in c.get("/login").get_data(as_text=True)


# ---------------------------------------------------------------- dashboard
def test_dashboard_without_metrics_shows_hint_instead_of_numbers(client):
    login(client)
    body = client.get("/dashboard").get_data(as_text=True)
    assert "Indicadores ainda não gerados" in body


def test_dashboard_reads_real_metrics_file(app, client, tmp_path):
    import json
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "metrics.json").write_text(json.dumps({
        "generated_at": "2026-11-06 15:00",
        "tests": {"total": 10, "passed": 10, "failed": 0, "skipped": 0, "coverage": 0.9},
        "quality_sample": {"overall_conformity": 0.5, "rules_failed": 6},
        "quality_full_base": {"overall_conformity": 0.99, "rules_approved": 5, "rules_total": 6,
                              "verdict": "LIBERADA COM RESSALVAS", "checks_evaluated": 600,
                              "rows": 100000},
        "quality_full_rules": [{"id": "QC06", "name": "x", "dimension": "Consistência",
                                "conformity": 0.96, "status": "REPROVADA", "failed": 4}],
        "kanban": {"columns": {"A fazer": 1, "Em andamento": 0, "Em revisão": 2, "Feito": 0},
                   "total_stories": 3, "sprint_points": 21, "done_points": 0},
        "maturity": [{"area": "Gestão de Requisitos", "ratings": ["L", "P", "F"]}],
        "model": {"roc_auc": 0.914, "recall": 0.844},
    }), encoding="utf-8")
    login(client)
    body = client.get("/dashboard").get_data(as_text=True)
    assert "10/10" in body and "90,0%" in body and "QC06" in body and "Gestão de Requisitos" in body
    assert "AUC 0,91" in body and "semi-sintética" in body


def test_root_redirects_by_auth_state(client):
    assert client.get("/").headers["Location"].endswith("/login")
    login(client)
    assert client.get("/").headers["Location"].endswith("/dashboard")


def test_unknown_page_returns_404(client):
    assert client.get("/nao-existe").status_code == 404
