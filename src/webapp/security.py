"""Proteções transversais: CSRF, redirecionamento seguro, limite de tentativas e cabeçalhos."""
from __future__ import annotations

import hmac
import secrets
import time
from collections import defaultdict, deque
from urllib.parse import urlsplit

from flask import abort, request, session

CSRF_FIELD = "csrf_token"


# ---------------------------------------------------------------- CSRF
def csrf_token() -> str:
    """Token por sessão, incluído como campo oculto em todo formulário POST."""
    if CSRF_FIELD not in session:
        session[CSRF_FIELD] = secrets.token_urlsafe(32)
    return session[CSRF_FIELD]


def verify_csrf() -> None:
    if request.method != "POST":
        return
    sent = request.form.get(CSRF_FIELD, "")
    expected = session.get(CSRF_FIELD, "")
    if not expected or not hmac.compare_digest(sent, expected):
        abort(400, description="Sessão expirada ou formulário inválido. Recarregue a página.")


# ---------------------------------------------------------------- redirecionamento
def safe_next(target: str | None, default: str) -> str:
    """Aceita apenas caminhos internos (evita open redirect via ?next=https://site-malicioso)."""
    if not target:
        return default
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or not target.startswith("/") or target.startswith("//") \
            or "\\" in target:
        return default
    return target


# ---------------------------------------------------------------- força bruta
class LoginRateLimiter:
    """Bloqueia temporariamente após N falhas na janela. Em memória: vale por processo
    (suficiente para execução local; em produção use Redis ou o proxy reverso)."""

    def __init__(self, max_failures: int = 5, window_seconds: int = 900):
        self.max_failures = max_failures
        self.window = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, now: float) -> deque[float]:
        q = self._failures[key]
        while q and now - q[0] > self.window:
            q.popleft()
        return q

    def retry_after(self, key: str, now: float | None = None) -> int:
        now = time.monotonic() if now is None else now
        q = self._prune(key, now)
        if len(q) < self.max_failures:
            return 0
        return max(1, int(self.window - (now - q[0])))

    def record_failure(self, key: str, now: float | None = None) -> None:
        now = time.monotonic() if now is None else now
        self._prune(key, now).append(now)

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)


# ---------------------------------------------------------------- cabeçalhos
APP_CSP = (
    "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
    "form-action 'self'; frame-ancestors 'none'; base-uri 'self'"
)


def apply_security_headers(response, is_legacy_panel: bool = False):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    if not is_legacy_panel:
        # Os painéis legados dependem de CDNs (Tailwind, Chart.js, Lucide); por isso a
        # CSP estrita vale só para as páginas novas. Ver docs/peer_review_simulation.md.
        response.headers.setdefault("Content-Security-Policy", APP_CSP)
    return response
