"""Savings goal operations and contribution estimates."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from src.database import get_connection
from src.transactions import from_paise, to_paise


def _nonnegative_paise(value: Any, label: str) -> int:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Enter a valid {label}.") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{label.capitalize()} cannot be negative.")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def add_goal(name: str, target: Any, saved: Any, target_date: str,
             description: str = "") -> int:
    if not name.strip():
        raise ValueError("Goal name is required.")
    target_paise = to_paise(target)
    saved_paise = _nonnegative_paise(saved, "saved amount")
    if saved_paise > target_paise:
        raise ValueError("Current savings cannot exceed the target amount.")
    try:
        date.fromisoformat(target_date)
    except ValueError:
        raise ValueError("Enter a valid target date.") from None
    with get_connection() as connection:
        cursor = connection.execute(
            """INSERT INTO savings_goals(name, target_paise, saved_paise, target_date, description)
               VALUES (?, ?, ?, ?, ?)""",
            (name.strip(), target_paise, saved_paise, target_date, description.strip()),
        )
        return int(cursor.lastrowid)


def get_goals() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM savings_goals ORDER BY target_date").fetchall()
    result = []
    for row in rows:
        remaining = row["target_paise"] - row["saved_paise"]
        days_until_target = (date.fromisoformat(row["target_date"]) - date.today()).days
        days = max(days_until_target, 1)
        months = max(days / 30.4375, 1 / 30.4375)
        result.append({
            **dict(row), "target": from_paise(row["target_paise"]),
            "saved": from_paise(row["saved_paise"]),
            "remaining": from_paise(remaining),
            "progress": row["saved_paise"] / row["target_paise"],
            "monthly_contribution": from_paise(remaining) / months,
            "overdue": days_until_target < 0 and remaining > 0,
        })
    return result


def update_goal_progress(goal_id: int, saved: Any) -> None:
    saved_paise = _nonnegative_paise(saved, "saved amount")
    with get_connection() as connection:
        row = connection.execute(
            "SELECT target_paise FROM savings_goals WHERE id = ?", (goal_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Savings goal was not found.")
        if saved_paise > row["target_paise"]:
            raise ValueError("Current savings cannot exceed the target amount.")
        connection.execute(
            "UPDATE savings_goals SET saved_paise = ? WHERE id = ?",
            (saved_paise, goal_id),
        )


def delete_goal(goal_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
        if cursor.rowcount == 0:
            raise ValueError("Savings goal was not found.")
