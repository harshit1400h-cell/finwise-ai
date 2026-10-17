import sqlite3

from src.database import get_connection, init_db, set_setting, get_settings


def test_database_initializes_all_tables(db_path):
    with get_connection() as connection:
        tables = {
            row["name"] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert {"transactions", "budgets", "savings_goals", "settings"} <= tables
    init_db()


def test_settings_upsert(db_path):
    set_setting("theme", "green")
    set_setting("theme", "light")
    assert get_settings()["theme"] == "light"


def test_transaction_storage_uses_integer_paise(db_path):
    from src.transactions import add_transaction, get_transaction

    transaction_id = add_transaction("2025-01-02", "Expense", "10.15",
                                     "Food", "Lunch")
    assert get_transaction(transaction_id)["amount_paise"] == 1015
