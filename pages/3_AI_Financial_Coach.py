from datetime import date, timedelta

import streamlit as st

from src.ai_coach import AIServiceError, ask_coach
from src.analytics import monthly_summary, period_dates
from src.budget_service import get_budgets
from src.database import init_db
from src.goals import get_goals
from src.transactions import get_transactions

init_db()
st.title("✨ AI Financial Coach")
st.caption("Personalized, data-grounded ideas. Suggestions are estimates, not regulated financial advice.")
month = st.date_input("Analyze month", value=date.today().replace(day=1)).strftime("%Y-%m")
start, end = period_dates(month)
transactions = get_transactions(start, end)
budgets = get_budgets(month)
goals = get_goals()
previous_start, previous_end = period_dates(
    (date.fromisoformat(start) - timedelta(days=1)).strftime("%Y-%m")
)
previous = get_transactions(previous_start, previous_end)
current_summary = monthly_summary(transactions)
previous_summary = monthly_summary(previous)
st.info(f"{month}: ₹{current_summary['expenses']:,.2f} expenses; previous month: "
        f"₹{previous_summary['expenses']:,.2f}. These totals are calculated from your records.")

examples = [
    "Where did I spend the most this month?",
    "Suggest realistic ways I can reduce expenses.",
    "Create a budget plan for next month.",
    "What happens if I reduce food expenses by 15%?",
]
question = st.selectbox("Try a question", examples)
with st.form("ask_coach"):
    custom_question = st.text_input("Ask about your finances", value=question)
    submitted = st.form_submit_button("Get insights", type="primary")
if submitted:
    if not transactions:
        st.warning("Record transactions for this month first so the coach can use your actual data.")
    else:
        with st.spinner("Preparing an insight from your summarized financial data..."):
            try:
                result = ask_coach(custom_question, transactions, budgets, previous, goals)
                st.subheader("Summary")
                st.write(result["summary"])
                st.subheader("Ideas to consider")
                for recommendation in result["recommendations"]:
                    st.markdown(f"- {recommendation}")
                st.caption(result["estimate_disclaimer"])
                st.session_state["latest_ai_insight"] = (
                    result["summary"] + "\n\n" + "\n".join(result["recommendations"])
                )
            except AIServiceError as error:
                st.error(str(error))
            except ValueError as error:
                st.error(str(error))
st.caption("Gemini receives computed summaries for the selected and previous month, "
           "selected-month budgets, and recorded savings goal totals and dates. "
           "Descriptions and receipt images are not sent. Do not enter credentials.")
