from datetime import date, timedelta

import streamlit as st

from src.analytics import category_totals, period_dates
from src.budget_service import get_budgets, remove_budget, set_budget
from src.database import init_db
from src.transactions import CATEGORIES, get_transactions

init_db()
st.title("🎯 Budgets")
st.caption("Create category spending limits. Usage and warnings are calculated from recorded expenses.")
month = st.date_input("Budget month", value=date.today().replace(day=1)).strftime("%Y-%m")

with st.form("set_budget"):
    category = st.selectbox("Category", CATEGORIES)
    limit = st.number_input("Monthly limit (₹)", min_value=0.0, step=500.0, format="%.2f")
    submitted = st.form_submit_button("Save or update budget", type="primary")
if submitted:
    try:
        set_budget(month, category, limit)
        st.success(f"{category} budget saved for {month}.")
        st.rerun()
    except ValueError as error:
        st.error(str(error))
    except Exception:
        st.error("Could not save the budget. Check the local database and try again.")

st.subheader(f"Budget limits · {month}")
budgets = get_budgets(month)
if not budgets:
    st.info("No budgets for this month yet.")
for budget in budgets:
    col1, col2, col3 = st.columns([3, 4, 1])
    col1.markdown(f"**{budget['category']}**")
    col1.caption(f"₹{budget['spent']:,.2f} spent · ₹{budget['remaining']:,.2f} remaining "
                 f"of ₹{budget['limit']:,.2f}")
    if budget["limit_paise"] == 0:
        col2.warning("Zero limit: any spending exceeds this budget.")
    else:
        col2.progress(min(max(budget["utilization"] / 100, 0), 1),
                      text=f"{budget['utilization']:.1f}% used")
        if budget["utilization"] >= 100:
            col2.error("Budget exceeded")
        elif budget["utilization"] >= 80:
            col2.warning("Approaching limit")
    if col3.button("Remove", key=f"remove_{budget['id']}"):
        st.session_state[f"confirm_budget_{budget['id']}"] = True
    if st.session_state.get(f"confirm_budget_{budget['id']}", False):
        if col3.button("Confirm removal", key=f"confirm_remove_{budget['id']}"):
            try:
                remove_budget(budget["id"])
                st.success("Budget removed.")
                st.rerun()
            except Exception:
                st.error("Could not remove the budget.")

previous_month = (date.fromisoformat(month + "-01") - timedelta(days=1)).strftime("%Y-%m")
current_start, current_end = period_dates(month)
previous_start, previous_end = period_dates(previous_month)
current_spending = category_totals(get_transactions(current_start, current_end))
previous_spending = category_totals(get_transactions(previous_start, previous_end))
current_by_category = dict(zip(current_spending["category"], current_spending["amount"]))
previous_by_category = dict(zip(previous_spending["category"], previous_spending["amount"]))
compared_categories = sorted(set(current_by_category) | set(previous_by_category))
st.subheader(f"Recorded spending comparison · {previous_month} vs {month}")
if compared_categories:
    st.dataframe([{
        "Category": category,
        f"{previous_month} (₹)": previous_by_category.get(category, 0.0),
        f"{month} (₹)": current_by_category.get(category, 0.0),
        "Change (₹)": current_by_category.get(category, 0.0)
                     - previous_by_category.get(category, 0.0),
    } for category in compared_categories], hide_index=True, width="stretch")
else:
    st.info("No expense transactions are recorded in either month.")
