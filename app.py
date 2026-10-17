import streamlit as st
import plotly.express as px
from datetime import date
from dotenv import load_dotenv

from src.analytics import category_totals, monthly_summary, monthly_trends, period_dates
from src.budget_service import get_budgets
from src.database import init_db
from src.goals import get_goals
from src.transactions import get_transactions


st.set_page_config(page_title="FinWise AI | Money, made clearer",
                   page_icon="💸", layout="wide")
load_dotenv()
init_db()

st.markdown(
    """
    <style>
    .stApp { background: #f5f8f6; }
    [data-testid="stSidebar"] { background: #102d25; }
    [data-testid="stSidebar"] * { color: #f4faf6; }
    div[data-testid="stMetric"] {
        background: #ffffff; padding: 18px; border: 1px solid #e6eee8;
        border-radius: 14px;
    }
    h1, h2, h3 { color: #173c30; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("💸 FinWise AI")
st.caption("A clearer view of your money — private, local-first, and built around your data.")
today = date.today()
month = st.sidebar.date_input("Dashboard month", value=today.replace(day=1)).strftime("%Y-%m")
start_date, end_date = period_dates(month)
selected_dates = st.sidebar.date_input(
    "Transaction date range",
    value=(date.fromisoformat(start_date), date.fromisoformat(end_date)),
)
if len(selected_dates) == 2:
    selected_start = max(selected_dates[0].isoformat(), start_date)
    selected_end = min(selected_dates[1].isoformat(), end_date)
else:
    selected_start, selected_end = start_date, end_date
transactions = (get_transactions(selected_start, selected_end)
               if selected_start <= selected_end else [])
all_transactions = get_transactions()
summary = monthly_summary(transactions)
budgets = get_budgets(month)
remaining_budget = sum(budget["remaining"] for budget in budgets)

if not all_transactions:
    st.info("Welcome! Add your first transaction to see your real spending and income here.")
    st.page_link("pages/1_Transactions.py", label="Open Transactions", icon="🧾")
else:
    metrics = st.columns(4)
    metrics[0].metric("Income this month", f"₹{summary['income']:,.2f}")
    metrics[1].metric("Expenses this month", f"₹{summary['expenses']:,.2f}")
    metrics[2].metric("Net cash flow", f"₹{summary['net_cash_flow']:,.2f}",
                      help="Income minus recorded expenses; not an account balance or confirmed savings.")
    metrics[3].metric("Budget remaining", f"₹{remaining_budget:,.2f}",
                      help="Sum of category budget limits less spending in those budgeted categories.")

    goals = get_goals()
    active_goals = [goal for goal in goals if goal["remaining"] > 0]
    if active_goals:
        average_progress = sum(goal["progress"] for goal in active_goals) / len(active_goals)
        st.progress(min(max(average_progress, 0), 1),
                    text=f"Savings goal progress (average of {len(active_goals)} active goals): "
                         f"{average_progress:.0%}")
        st.caption("Goal progress reflects amounts you explicitly entered, not inferred savings.")

    left, right = st.columns(2)
    category_data = category_totals(transactions)
    with left:
        st.subheader("Spending by category")
        if category_data.empty:
            st.info("No expenses recorded for this month yet.")
        else:
            st.plotly_chart(px.pie(category_data, names="category", values="amount",
                                   hole=0.55, title="Recorded expenses"),
                            width="stretch")
    with right:
        st.subheader("Income versus expenses")
        chart_data = monthly_trends(all_transactions)
        if chart_data.empty:
            st.info("Add transactions to build your monthly trend.")
        else:
            st.plotly_chart(px.bar(chart_data, x="month", y=["Income", "Expense"],
                                   barmode="group", title="Recent monthly cash flow"),
                            width="stretch")

    st.subheader("Budget utilization")
    if not budgets:
        st.info("No category budgets set for this month.")
    for budget in budgets:
        label = (f"{budget['category']} · ₹{budget['spent']:,.2f} of "
                 f"₹{budget['limit']:,.2f}")
        st.write(label)
        if budget["limit_paise"] == 0:
            st.warning(f"{budget['category']}: zero budget set; any spending exceeds it.")
        else:
            utilization = budget["utilization"] / 100
            st.progress(min(max(utilization, 0), 1),
                        text=f"{budget['utilization']:.0f}% used")
            if budget["utilization"] >= 100:
                st.error(f"{budget['category']} budget exceeded.")
            elif budget["utilization"] >= 80:
                st.warning(f"You're approaching the {budget['category']} budget.")

    st.subheader("Recent transactions")
    st.dataframe([{
        "Date": row["transaction_date"], "Type": row["transaction_type"],
        "Category": row["category"], "Description": row["description"],
        "Amount": f"₹{row['amount_paise'] / 100:,.2f}",
    } for row in all_transactions[:8]], width="stretch", hide_index=True)
