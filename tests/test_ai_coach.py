import sys
import types

import pytest

from src.ai_coach import (
    AIServiceError, ask_coach, build_financial_context, calculate_what_if,
)
from src.transactions import add_transaction, get_transactions


def test_missing_gemini_key_is_actionable(db_path, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(AIServiceError, match="GEMINI_API_KEY"):
        ask_coach("How am I doing?", [], [])


def test_api_failure_is_reported_without_raw_exception(db_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class BrokenModels:
        def generate_content(self, **_kwargs):
            raise RuntimeError("private network detail")

    fake_google = types.ModuleType("google")
    fake_google.genai = types.SimpleNamespace(Client=lambda **_kwargs:
                                               types.SimpleNamespace(models=BrokenModels()))
    monkeypatch.setitem(sys.modules, "google", fake_google)
    with pytest.raises(AIServiceError) as error:
        ask_coach("How am I doing?", [], [])
    assert "private network detail" not in str(error.value)


def test_context_uses_computed_current_and_previous_totals(db_path):
    add_transaction("2025-04-05", "Expense", 40, "Food", "Lunch")
    add_transaction("2025-03-05", "Expense", 20, "Travel", "Bus")
    current = get_transactions("2025-04-01", "2025-04-30")
    previous = get_transactions("2025-03-01", "2025-03-31")
    context = build_financial_context(current, [], previous)
    assert context["expense_inr"] == 40
    assert context["previous_month"]["expense_inr"] == 20
    assert context["expense_categories_inr"] == [
        {"category": "Food", "amount": 40.0, "percentage_of_expenses": 100.0}
    ]
    assert context["budget_totals_inr"] == {"limit": 0, "spent": 0, "remaining": 0}


def test_context_includes_only_summarized_savings_goal_data(db_path):
    goal = {
        "name": "Emergency fund", "target": 10000, "saved": 1000,
        "remaining": 9000, "target_date": "2026-12-31", "description": "private note",
    }
    context = build_financial_context([], [], savings_goals=[goal])
    assert context["savings_goals"] == [{
        "name": "Emergency fund", "target_inr": 10000, "saved_inr": 1000,
        "remaining_inr": 9000, "target_date": "2026-12-31",
    }]


def test_what_if_scenario_is_calculated_from_recorded_expenses(db_path):
    add_transaction("2025-04-05", "Expense", 200, "Food", "Groceries")
    add_transaction("2025-04-06", "Expense", 100, "Travel", "Bus")
    transactions = get_transactions("2025-04-01", "2025-04-30")
    scenario = calculate_what_if("Reduce Food expenses by 15%", transactions)
    assert scenario == {
        "category": "Food",
        "reduction_percentage": 15.0,
        "current_category_expense_inr": 200.0,
        "estimated_category_expense_inr": 170.0,
        "estimated_monthly_expenses_inr": 270.0,
        "estimated_monthly_savings_inr": 30.0,
    }
