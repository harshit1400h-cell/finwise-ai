"""Deterministic financial summaries and chart data."""

from datetime import date
from typing import Any

import pandas as pd

from src.transactions import from_paise


def monthly_summary(transactions: list[dict[str, Any]]) -> dict[str, float]:
    income = sum(row["amount_paise"] for row in transactions
                 if row["transaction_type"] == "Income")
    expenses = sum(row["amount_paise"] for row in transactions
                   if row["transaction_type"] == "Expense")
    return {
        "income": from_paise(income),
        "expenses": from_paise(expenses),
        "net_cash_flow": from_paise(income - expenses),
    }


def category_totals(transactions: list[dict[str, Any]]) -> pd.DataFrame:
    totals: dict[str, int] = {}
    for row in transactions:
        if row["transaction_type"] == "Expense":
            totals[row["category"]] = totals.get(row["category"], 0) + row["amount_paise"]
    return pd.DataFrame(
        [{"category": category, "amount": from_paise(amount)}
         for category, amount in sorted(totals.items(), key=lambda item: item[1], reverse=True)],
        columns=["category", "amount"],
    )


def monthly_trends(transactions: list[dict[str, Any]], months: int = 6) -> pd.DataFrame:
    end = date.today().replace(day=1)
    start_month = end.month - months + 1
    year = end.year + (start_month - 1) // 12
    month = (start_month - 1) % 12 + 1
    start = date(year, month, 1).isoformat()
    frame = pd.DataFrame(transactions)
    if frame.empty:
        return pd.DataFrame(columns=["month", "Income", "Expense"])
    frame = frame[(frame["transaction_date"] >= start)
                  & (frame["transaction_date"] <= date.today().isoformat())].copy()
    frame["month"] = frame["transaction_date"].str[:7]
    frame["amount"] = frame["amount_paise"] / 100
    result = frame.pivot_table(index="month", columns="transaction_type",
                               values="amount", aggfunc="sum", fill_value=0)
    result = result.reindex(columns=["Income", "Expense"], fill_value=0)
    return result.reset_index()


def period_dates(month: str) -> tuple[str, str]:
    try:
        period = date.fromisoformat(month + "-01")
    except ValueError:
        raise ValueError("Month must use YYYY-MM format.") from None
    following = date(period.year + (period.month == 12), period.month % 12 + 1, 1)
    return period.isoformat(), date.fromordinal(following.toordinal() - 1).isoformat()
