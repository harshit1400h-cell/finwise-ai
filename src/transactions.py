"""Validated transaction operations. Monetary amounts are stored as integer paise."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from src.database import get_connection


CATEGORIES = [
    "Food", "Groceries", "Transport", "Education", "Shopping", "Rent",
    "Utilities", "Healthcare", "Entertainment", "Travel", "Salary",
    "Freelance Income", "Other",
]
PAYMENT_METHODS = ["Cash", "UPI", "Debit card", "Credit card", "Bank transfer", "Other"]
TRANSACTION_TYPES = ["Income", "Expense"]


def to_paise(amount: Any) -> int:
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid amount.") from None
    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be greater than zero.")
    return int((value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def from_paise(amount_paise: int) -> float:
    return amount_paise / 100


def _validate_fields(transaction_date: str, transaction_type: str, category: str,
                     description: str, payment_method: str) -> None:
    try:
        date.fromisoformat(transaction_date)
    except (TypeError, ValueError):
        raise ValueError("Enter a valid transaction date.") from None
    if transaction_type not in TRANSACTION_TYPES:
        raise ValueError("Transaction type must be Income or Expense.")
    if not category.strip() or not description.strip() or not payment_method.strip():
        raise ValueError("Category, description, and payment method are required.")


def add_transaction(transaction_date: str, transaction_type: str, amount: Any,
                    category: str, description: str, payment_method: str = "Other",
                    merchant: str = "") -> int:
    _validate_fields(transaction_date, transaction_type, category, description, payment_method)
    amount_paise = to_paise(amount)
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO transactions
               (transaction_date, transaction_type, amount_paise, category,
                description, payment_method, merchant)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (transaction_date, transaction_type, amount_paise, category.strip(),
             description.strip(), payment_method.strip(), merchant.strip()),
        )
        return int(cursor.lastrowid)


def get_transactions(start_date: str | None = None, end_date: str | None = None,
                     transaction_type: str | None = None,
                     category: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT * FROM transactions WHERE 1 = 1"
    parameters: list[Any] = []
    if start_date:
        query += " AND transaction_date >= ?"
        parameters.append(start_date)
    if end_date:
        query += " AND transaction_date <= ?"
        parameters.append(end_date)
    if transaction_type and transaction_type != "All":
        query += " AND transaction_type = ?"
        parameters.append(transaction_type)
    if category and category != "All":
        query += " AND category = ?"
        parameters.append(category)
    query += " ORDER BY transaction_date DESC, id DESC"
    with get_connection() as connection:
        return [dict(row) for row in connection.execute(query, parameters).fetchall()]


def get_transaction(transaction_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM transactions WHERE id = ?", (transaction_id,)
        ).fetchone()
    return dict(row) if row else None


def update_transaction(transaction_id: int, transaction_date: str,
                       transaction_type: str, amount: Any, category: str,
                       description: str, payment_method: str = "Other",
                       merchant: str = "") -> None:
    _validate_fields(transaction_date, transaction_type, category, description, payment_method)
    with get_connection() as connection:
        cursor = connection.execute(
            """UPDATE transactions SET transaction_date = ?, transaction_type = ?,
               amount_paise = ?, category = ?, description = ?, payment_method = ?,
               merchant = ? WHERE id = ?""",
            (transaction_date, transaction_type, to_paise(amount), category.strip(),
             description.strip(), payment_method.strip(), merchant.strip(), transaction_id),
        )
        if cursor.rowcount == 0:
            raise ValueError("Transaction was not found.")


def delete_transaction(transaction_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        if cursor.rowcount == 0:
            raise ValueError("Transaction was not found.")
