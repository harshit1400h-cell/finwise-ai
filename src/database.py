"""SQLite persistence for the local, single-user FinWise AI application."""

import os
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "finwise.db"


def database_path() -> Path:
    return Path(os.environ.get("FINWISE_DB_PATH", str(DEFAULT_DB_PATH))).expanduser()


def get_connection() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    """Create the local database and its tables on first launch."""
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date TEXT NOT NULL,
                transaction_type TEXT NOT NULL CHECK (transaction_type IN ('Income', 'Expense')),
                amount_paise INTEGER NOT NULL CHECK (amount_paise > 0),
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                payment_method TEXT NOT NULL DEFAULT 'Other',
                merchant TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_date
                ON transactions(transaction_date);
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month TEXT NOT NULL,
                category TEXT NOT NULL,
                limit_paise INTEGER NOT NULL CHECK (limit_paise >= 0),
                UNIQUE(month, category)
            );
            CREATE TABLE IF NOT EXISTS savings_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                target_paise INTEGER NOT NULL CHECK (target_paise > 0),
                saved_paise INTEGER NOT NULL DEFAULT 0 CHECK (saved_paise >= 0),
                target_date TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )


def get_settings() -> dict[str, str]:
    with get_connection() as connection:
        rows = connection.execute("SELECT key, value FROM settings ORDER BY key").fetchall()
    return {row["key"]: row["value"] for row in rows}


def set_setting(key: str, value: str) -> None:
    if not key.strip():
        raise ValueError("Setting key is required.")
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO settings(key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key.strip(), value),
        )
