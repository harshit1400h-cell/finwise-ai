from datetime import date

import streamlit as st

from src.analytics import category_totals, monthly_summary, period_dates
from src.budget_service import get_budgets
from src.database import init_db
from src.report_generator import pdf_report, transactions_csv
from src.transactions import get_transactions

init_db()
st.title("📊 Reports")
month = st.date_input("Reporting month", value=date.today().replace(day=1)).strftime("%Y-%m")
start, end = period_dates(month)
transactions = get_transactions(start, end)
budgets = get_budgets(month)
summary = monthly_summary(transactions)
left, middle, right = st.columns(3)
left.metric("Income", f"₹{summary['income']:,.2f}")
middle.metric("Expenses", f"₹{summary['expenses']:,.2f}")
right.metric("Net cash flow", f"₹{summary['net_cash_flow']:,.2f}",
             help="Not confirmed savings or account balance.")
st.subheader("Category-wise expenses")
categories = category_totals(transactions)
if categories.empty:
    st.info("No expenses recorded for this period.")
else:
    st.dataframe(categories.rename(columns={"category": "Category", "amount": "Amount (₹)"}),
                 hide_index=True, width="stretch")
st.subheader("Budget performance")
if budgets:
    st.dataframe([{
        "Category": item["category"], "Limit (₹)": item["limit"],
        "Spent (₹)": item["spent"], "Remaining (₹)": item["remaining"],
        "Utilization (%)": item["utilization"],
    } for item in budgets], hide_index=True, width="stretch")
else:
    st.info("No budgets set for this month.")
csv_bytes = transactions_csv(transactions).encode("utf-8-sig")
st.download_button("Download transactions CSV", csv_bytes,
                   file_name=f"finwise-transactions-{month}.csv", mime="text/csv")
insights = st.session_state.get("latest_ai_insight", "")
try:
    pdf_bytes = pdf_report(month, transactions, budgets, insights)
    st.download_button("Download monthly PDF report", pdf_bytes,
                       file_name=f"finwise-report-{month}.pdf", mime="application/pdf")
except Exception:
    st.error("Could not generate the PDF report. Check the ReportLab installation.")
st.caption("Net cash flow is calculated as income less recorded expenses. This report is not financial advice.")
