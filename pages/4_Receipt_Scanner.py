from datetime import date

import streamlit as st

from src.database import init_db
from src.receipt_scanner import ReceiptError, extract_receipt
from src.transactions import CATEGORIES, PAYMENT_METHODS, add_transaction

init_db()
st.title("📸 Receipt Scanner")
st.caption("Local OCR may make mistakes. Always review every field; nothing is saved until you confirm.")
uploaded = st.file_uploader("Upload a JPG, JPEG, or PNG receipt (max 5 MB)",
                            type=["jpg", "jpeg", "png"])
if uploaded is not None:
    raw = uploaded.getvalue()
    st.image(raw, caption="Uploaded receipt", width="stretch")
    if st.button("Extract receipt details", type="primary"):
        with st.spinner("Reading receipt locally..."):
            try:
                st.session_state["receipt_data"] = extract_receipt(raw)
                st.session_state["receipt_name"] = uploaded.name
            except ReceiptError as error:
                st.error(str(error))
    receipt = st.session_state.get("receipt_data")
    if receipt and st.session_state.get("receipt_name") == uploaded.name:
        if receipt["amount_needs_review"]:
            st.warning("The total is ambiguous or could not be detected. Verify it carefully.")
        with st.form("verify_receipt"):
            merchant = st.text_input("Merchant", value=receipt["merchant"])
            date_value = st.date_input(
                "Transaction date",
                value=date.fromisoformat(receipt["date"]),
            )
            amount = st.number_input("Verified amount (₹)", min_value=0.0,
                                     value=float(receipt["amount"] or 0), step=10.0,
                                     format="%.2f")
            category = st.selectbox("Category", CATEGORIES,
                index=CATEGORIES.index(receipt["category"]))
            payment = st.selectbox("Payment method", PAYMENT_METHODS)
            description = st.text_input("Description", value=receipt["description"])
            verified = st.checkbox("I reviewed and verified the amount and details.")
            save = st.form_submit_button("Save verified expense")
        with st.expander("OCR text for review"):
            if receipt["line_items"]:
                st.write("Possible line items:", receipt["line_items"])
            st.text(receipt["extracted_text"] or "No text was extracted.")
        if save:
            if not verified:
                st.error("Please confirm that you reviewed the extracted details.")
            else:
                try:
                    add_transaction(date_value.isoformat(), "Expense", amount, category,
                                    description, payment, merchant)
                    st.success("Verified receipt transaction saved.")
                    del st.session_state["receipt_data"]
                    del st.session_state["receipt_name"]
                except ValueError as error:
                    st.error(str(error))
                except Exception:
                    st.error("Could not save the verified transaction. Check the local database.")
st.caption("Images are processed in memory and are not stored by FinWise AI. OCR uses the local Tesseract application.")
