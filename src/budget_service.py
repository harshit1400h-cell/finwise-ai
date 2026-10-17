"""Monthly and category budget management."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date
from typing import Any

from src.database import get_connection
from src.transactions import from_paise


def set_budget(month: str, category: str, limit: Any) -> None:
    try:
        date.fromisoformat(month + "-01")
    except ValueError:
        raise ValueError("Month must use YYYY-MM format.")
    if not category.strip():
        raise ValueError("Budget category is required.")
    try:
        amount = Decimal(str(limit))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid budget limit.") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError("Budget limit cannot be negative.")
    amount_paise = int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    with get_connection() as connection:
        connection.execute(
            """INSERT INTO budgets(month, category, limit_paise) VALUES (?, ?, ?)
               ON CONFLICT(month, category) DO UPDATE SET limit_paise = excluded.limit_paise""",
            (month, category.strip(), amount_paise),
        )


def remove_budget(budget_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM budgets WHERE id = ?", (budget_id,))
        if cursor.rowcount == 0:
            raise ValueError("Budget was not found.")


def get_budgets(month: str) -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM budgets WHERE month = ? ORDER BY category", (month,)
        ).fetchall()
        spending = connection.execute(
            """SELECT category, SUM(amount_paise) AS spent_paise FROM transactions
               WHERE transaction_type = 'Expense' AND substr(transaction_date, 1, 7) = ?
               GROUP BY category""",
            (month,),
        ).fetchall()
    spent_by_category = {row["category"]: row["spent_paise"] for row in spending}
    result = []
    for row in rows:
        spent = spent_by_category.get(row["category"], 0)
        limit = row["limit_paise"]
        result.append({
            "id": row["id"], "month": row["month"], "category": row["category"],
            "limit_paise": limit, "spent_paise": spent,
            "limit": from_paise(limit), "spent": from_paise(spent),
            "remaining": from_paise(limit - spent),
            "utilization": (spent / limit * 100) if limit else None,
        })
    return result


def total_budget(month: str) -> float:
    return sum(item["limit"] for item in get_budgets(month))
