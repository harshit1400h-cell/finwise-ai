from src.analytics import category_totals, monthly_summary, period_dates
from src.transactions import add_transaction, get_transactions


def test_income_expense_and_net_cash_flow(db_path):
    add_transaction("2025-01-02", "Income", 2500, "Salary", "Pay")
    add_transaction("2025-01-03", "Expense", 450.25, "Food", "Groceries")
    add_transaction("2025-01-04", "Expense", 50, "Food", "Tea")
    rows = get_transactions("2025-01-01", "2025-01-31")
    assert monthly_summary(rows) == {
        "income": 2500.0, "expenses": 500.25, "net_cash_flow": 1999.75
    }
    categories = category_totals(rows)
    assert categories.to_dict(orient="records") == [{"category": "Food", "amount": 500.25}]


def test_period_dates_month_edges_and_invalid_input():
    assert period_dates("2024-02") == ("2024-02-01", "2024-02-29")
    assert period_dates("2025-12") == ("2025-12-01", "2025-12-31")


def test_empty_summary_is_zero(db_path):
    assert monthly_summary([]) == {"income": 0.0, "expenses": 0.0, "net_cash_flow": 0.0}
    assert category_totals([]).empty
