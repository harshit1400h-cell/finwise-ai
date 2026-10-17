"""Gemini financial coach using only summarized user-provided financial data."""

import json
import os
import re
from typing import Any

from src.analytics import category_totals, monthly_summary


class AIServiceError(RuntimeError):
    """A safe, user-displayable AI service error."""


def build_financial_context(transactions: list[dict[str, Any]],
                            budgets: list[dict[str, Any]],
                            previous_transactions: list[dict[str, Any]] | None = None,
                            savings_goals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    summary = monthly_summary(transactions)
    categories = category_totals(transactions)
    total_expenses = summary["expenses"]
    category_records = categories.to_dict(orient="records")
    for category in category_records:
        category["percentage_of_expenses"] = (
            category["amount"] / total_expenses * 100 if total_expenses else 0
        )
    context = {
        "transaction_count": len(transactions),
        "income_inr": summary["income"],
        "expense_inr": summary["expenses"],
        "net_cash_flow_inr": summary["net_cash_flow"],
        "expense_categories_inr": category_records,
        "budgets": [
            {"category": budget["category"], "limit_inr": budget["limit"],
             "spent_inr": budget["spent"], "remaining_inr": budget["remaining"]}
            for budget in budgets
        ],
        "budget_totals_inr": {
            "limit": sum(budget["limit"] for budget in budgets),
            "spent": sum(budget["spent"] for budget in budgets),
            "remaining": sum(budget["remaining"] for budget in budgets),
        },
    }
    if previous_transactions is not None:
        previous = monthly_summary(previous_transactions)
        context["previous_month"] = {
            "income_inr": previous["income"],
            "expense_inr": previous["expenses"],
            "net_cash_flow_inr": previous["net_cash_flow"],
        }
    if savings_goals is not None:
        context["savings_goals"] = [
            {"name": goal["name"], "target_inr": goal["target"],
             "saved_inr": goal["saved"], "remaining_inr": goal["remaining"],
             "target_date": goal["target_date"]}
            for goal in savings_goals
        ]
    return context


def calculate_what_if(question: str,
                      transactions: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Calculate simple percentage-reduction scenarios from recorded expense totals."""
    categories = category_totals(transactions)
    for _, row in categories.iterrows():
        pattern = (
            r"reduce\s+" + re.escape(row["category"]) +
            r"\s+(?:expenses?|spending)\s+by\s+(\d+(?:\.\d+)?)\s*%"
        )
        match = re.search(pattern, question, re.IGNORECASE)
        if not match:
            continue
        percentage = float(match.group(1))
        if percentage < 0 or percentage > 100:
            raise ValueError("A spending reduction must be between 0% and 100%.")
        summary = monthly_summary(transactions)
        savings = row["amount"] * percentage / 100
        return {
            "category": row["category"],
            "reduction_percentage": percentage,
            "current_category_expense_inr": row["amount"],
            "estimated_category_expense_inr": row["amount"] - savings,
            "estimated_monthly_expenses_inr": summary["expenses"] - savings,
            "estimated_monthly_savings_inr": savings,
        }
    return None


def ask_coach(question: str, transactions: list[dict[str, Any]],
              budgets: list[dict[str, Any]],
              previous_transactions: list[dict[str, Any]] | None = None,
              savings_goals: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise AIServiceError(
            "Gemini is not configured. Add GEMINI_API_KEY to your local .env file."
        )
    if not question.strip():
        raise ValueError("Enter a question for the financial coach.")

    context = build_financial_context(
        transactions, budgets, previous_transactions, savings_goals
    )
    scenario = calculate_what_if(question, transactions)
    if scenario:
        context["computed_what_if_scenario"] = scenario
    prompt = (
        "You are a beginner-friendly personal budgeting assistant, not a regulated "
        "financial adviser. Use only the supplied data; identify missing data rather "
        "than inventing facts. Any estimates must be labeled estimates. Never do "
        "arithmetic; use only the computed figures given. Return ONLY valid JSON with "
        'keys "summary" (string), "recommendations" (array of strings), and '
        '"estimate_disclaimer" (string). Keep the response concise.\n'
        f"Computed financial data in INR: {json.dumps(context, ensure_ascii=True)}\n"
        f"User question: {question.strip()}"
    )
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = response.text
        data = json.loads(text)
        if (not isinstance(data, dict) or not isinstance(data.get("summary"), str)
                or not isinstance(data.get("recommendations"), list)
                or not all(isinstance(item, str) for item in data["recommendations"])):
            raise ValueError("Unexpected response structure.")
        data.setdefault("estimate_disclaimer", "These are estimates, not financial advice.")
        if not isinstance(data["estimate_disclaimer"], str):
            raise ValueError("Unexpected disclaimer.")
        return data
    except Exception as exc:
        raise AIServiceError(
            "The AI coach could not complete this request. Check your API configuration "
            "and connection, then try again."
        ) from exc
