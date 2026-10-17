import pytest

from src.transactions import (
    add_transaction, delete_transaction, get_transaction, get_transactions,
    update_transaction,
)


def test_add_filter_edit_and_delete_transaction(db_path):
    first = add_transaction("2025-03-02", "Expense", 125.5, "Food", "Lunch")
    add_transaction("2025-04-02", "Income", 2000, "Salary", "Pay")
    assert [row["id"] for row in get_transactions("2025-03-01", "2025-03-31")] == [first]
    update_transaction(first, "2025-03-03", "Expense", "150.25",
                       "Groceries", "Market", "UPI", "Local shop")
    updated = get_transaction(first)
    assert updated["amount_paise"] == 15025
    assert updated["category"] == "Groceries"
    delete_transaction(first)
    assert get_transaction(first) is None


@pytest.mark.parametrize("amount", [0, -1, "not-money", "NaN", "Infinity"])
def test_transaction_requires_positive_finite_amount(db_path, amount):
    with pytest.raises(ValueError):
        add_transaction("2025-03-02", "Expense", amount, "Food", "Lunch")


def test_rejects_invalid_fields(db_path):
    with pytest.raises(ValueError):
        add_transaction("not-a-date", "Expense", 10, "Food", "Lunch")
    with pytest.raises(ValueError):
        add_transaction("2025-03-02", "Transfer", 10, "Food", "Lunch")


def test_sql_parameters_treat_search_values_as_data(db_path):
    add_transaction("2025-03-02", "Expense", 10, "Food", "x' OR 1=1 --")
    assert len(get_transactions(category="missing' OR 1=1 --")) == 0
