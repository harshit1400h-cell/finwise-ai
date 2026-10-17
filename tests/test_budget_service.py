import pytest

from src.budget_service import get_budgets, remove_budget, set_budget, total_budget
from src.transactions import add_transaction


def test_budget_usage_remaining_and_warning_values(db_path):
    set_budget("2025-05", "Food", 100)
    add_transaction("2025-05-05", "Expense", 75, "Food", "Groceries")
    budget = get_budgets("2025-05")[0]
    assert budget["spent"] == 75
    assert budget["remaining"] == 25
    assert budget["utilization"] == 75
    assert total_budget("2025-05") == 100


def test_zero_budget_and_empty_history_are_safe(db_path):
    set_budget("2025-05", "Food", 0)
    budget = get_budgets("2025-05")[0]
    assert budget["spent"] == 0
    assert budget["utilization"] is None
    add_transaction("2025-05-05", "Expense", 5, "Food", "Snack")
    assert get_budgets("2025-05")[0]["utilization"] is None


def test_budget_validation_and_removal(db_path):
    with pytest.raises(ValueError):
        set_budget("2025-13", "Food", 100)
    with pytest.raises(ValueError):
        set_budget("2025-05", "Food", -1)
    set_budget("2025-05", "Food", 100)
    budget_id = get_budgets("2025-05")[0]["id"]
    remove_budget(budget_id)
    assert get_budgets("2025-05") == []
