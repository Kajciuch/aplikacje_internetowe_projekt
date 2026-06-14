"""
Warstwa dostępu do bazy danych (SQLite, biblioteka standardowa sqlite3).

Wszystkie zapytania używają parametrów (?) zamiast sklejania stringów —
to chroni przed SQL Injection (wymóg bezpieczeństwa, etap 12).
"""

import sqlite3
from pathlib import Path
from flask import g, current_app


def get_db():
    """Zwraca połączenie z bazą, jedno na żądanie HTTP (trzymane w `g`)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        # Dzięki temu wiersze zachowują się jak słowniki: row["email"].
        g.db.row_factory = sqlite3.Row
        # Włączamy egzekwowanie kluczy obcych (SQLite ma to domyślnie wyłączone).
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    """Zamyka połączenie po zakończeniu żądania."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Tworzy tabele na podstawie schema.sql (jeśli jeszcze nie istnieją)."""
    db = get_db()
    schema_path = Path(current_app.root_path) / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


# --- Pomocnicze skróty na zapytania -----------------------------------------

def query_all(sql, params=()):
    """Zwraca listę wierszy."""
    return get_db().execute(sql, params).fetchall()


def query_one(sql, params=()):
    """Zwraca jeden wiersz albo None."""
    return get_db().execute(sql, params).fetchone()


def execute(sql, params=()):
    """Wykonuje INSERT/UPDATE/DELETE i zwraca lastrowid. Zatwierdza zmiany."""
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    return cur.lastrowid


def register_db(app):
    """Podpina zamykanie bazy i komendę CLI `flask init-db`."""
    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        """Inicjalizuje pustą bazę danych (tabele)."""
        init_db()
        print("Baza danych zainicjalizowana (tabele utworzone).")
