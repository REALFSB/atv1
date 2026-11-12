"""Persistência de usuários em SQLite. Senhas só existem como hash (scrypt via Werkzeug)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone

from flask import current_app, g
from werkzeug.security import check_password_hash, generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL
);
"""

# Hash de uma senha aleatória, usado quando o e-mail não existe: o tempo de resposta
# fica parecido com o de um usuário real, dificultando descobrir quais e-mails existem.
_DUMMY_HASH = generate_password_hash("datatrack-usuario-inexistente")


class UserExistsError(ValueError):
    """E-mail já cadastrado."""


@dataclass(frozen=True)
class User:
    id: int
    name: str
    email: str

    @property
    def first_name(self) -> str:
        return self.name.split()[0] if self.name.strip() else self.email


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    get_db().executescript(SCHEMA)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def create_user(name: str, email: str, password: str) -> User:
    db = get_db()
    email = normalize_email(email)
    try:
        cur = db.execute(
            "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (name.strip(), email, generate_password_hash(password),
             datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )
        db.commit()
    except sqlite3.IntegrityError as exc:
        raise UserExistsError(email) from exc
    return User(cur.lastrowid, name.strip(), email)


def get_user(user_id: int) -> User | None:
    row = get_db().execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(row["id"], row["name"], row["email"]) if row else None


def authenticate(email: str, password: str) -> User | None:
    """Devolve o usuário se e-mail e senha conferem; None caso contrário (sem dizer qual falhou)."""
    row = get_db().execute(
        "SELECT id, name, email, password_hash FROM users WHERE email = ?",
        (normalize_email(email),),
    ).fetchone()
    if row is None:
        check_password_hash(_DUMMY_HASH, password)
        return None
    if not check_password_hash(row["password_hash"], password):
        return None
    return User(row["id"], row["name"], row["email"])
