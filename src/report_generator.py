"""CSV and PDF report generation."""

from io import BytesIO
from typing import Any

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.analytics import category_totals, monthly_summary
from src.transactions import from_paise


def transactions_csv(transactions: list[dict[str, Any]]) -> str:
    columns = ["transaction_date", "transaction_type", "amount", "category",
               "description", "payment_method", "merchant"]
    rows = []
    for item in transactions:
        rows.append({
            "transaction_date": item["transaction_date"],
            "transaction_type": item["transaction_type"],
            "amount": f"{from_paise(item['amount_paise']):.2f}",
            "category": item["category"], "description": item["description"],
            "payment_method": item["payment_method"], "merchant": item["merchant"],
        })
    return pd.DataFrame(rows, columns=columns).to_csv(index=False)


def pdf_report(month: str, transactions: list[dict[str, Any]],
               budgets: list[dict[str, Any]], insights: str = "") -> bytes:
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, rightMargin=18 * mm,
                                 leftMargin=18 * mm, topMargin=18 * mm,
                                 bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("FinWise AI — Monthly Financial Report", styles["Title"]),
             Paragraph(f"Reporting period: {month}", styles["Normal"]), Spacer(1, 12)]
    summary = monthly_summary(transactions)
    data = [["Income", "Expenses", "Net cash flow"],
            [f"₹{summary['income']:,.2f}", f"₹{summary['expenses']:,.2f}",
             f"₹{summary['net_cash_flow']:,.2f}"]]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176B4D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story += [table, Spacer(1, 14), Paragraph("Spending by category", styles["Heading2"])]
    categories = category_totals(transactions)
    category_data = [["Category", "Expense (INR)"]]
    category_data += [[row["category"], f"₹{row['amount']:,.2f}"]
                      for _, row in categories.iterrows()]
    if len(category_data) == 1:
        category_data.append(["No expense transactions", "—"])
    category_table = Table(category_data, repeatRows=1, hAlign="LEFT")
    category_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176B4D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(category_table)
    story += [Spacer(1, 14), Paragraph("Budget performance", styles["Heading2"])]
    budget_data = [["Category", "Limit", "Spent", "Remaining"]]
    budget_data += [[item["category"], f"₹{item['limit']:,.2f}",
                     f"₹{item['spent']:,.2f}", f"₹{item['remaining']:,.2f}"]
                    for item in budgets]
    if len(budget_data) == 1:
        budget_data.append(["No budgets set", "—", "—", "—"])
    budget_table = Table(budget_data, repeatRows=1, hAlign="LEFT")
    budget_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176B4D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(budget_table)
    if insights:
        story += [Spacer(1, 14), Paragraph("AI-generated insights", styles["Heading2"]),
                  Paragraph(insights.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
                            styles["BodyText"])]
    story += [Spacer(1, 14), Paragraph(
        "Net cash flow is income minus recorded expenses; it is not confirmed savings "
        "or an account balance. AI suggestions are estimates, not regulated financial advice.",
        styles["Italic"])]
    document.build(story)
    return output.getvalue()
