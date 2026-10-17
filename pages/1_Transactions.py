from datetime import date

import pandas as pd
import streamlit as st

from src.database import init_db
from src.transactions import (
    CATEGORIES, PAYMENT_METHODS, TRANSACTION_TYPES, add_transaction,
    delete_transaction, get_transactions, get_transaction, update_transaction,
)

init_db()
st.title("🧾 Transactions")
st.caption("Search, filter, add, edit, and remove recorded transactions.")

with st.expander("Add a transaction", expanded=False):
    with st.form("add_transaction"):
        col1, col2, col3 = st.columns(3)
        transaction_date = col1.date_input("Date", value=date.today())
        transaction_type = col2.selectbox("Type", TRANSACTION_TYPES)
        amount = col3.number_input("Amount (₹)", min_value=0.01, step=50.0, format="%.2f")
        category = col1.selectbox("Category", CATEGORIES)
        payment_method = col2.selectbox("Payment method", PAYMENT_METHODS)
        merchant = col3.text_input("Merchant (optional)")
        description = st.text_input("Description")
        submitted = st.form_submit_button("Save transaction", type="primary")
    if submitted:
        try:
            add_transaction(transaction_date.isoformat(), transaction_type, amount,
                            category, description, payment_method, merchant)
            st.success("Transaction saved.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))
        except Exception:
            st.error("Could not save the transaction. Check the local database and try again.")

st.subheader("Transaction history")
filters = st.columns(4)
from_date = filters[0].date_input("From", value=date.today().replace(day=1))
to_date = filters[1].date_input("To", value=date.today())
type_filter = filters[2].selectbox("Type", ["All", *TRANSACTION_TYPES])
category_filter = filters[3].selectbox("Category", ["All", *CATEGORIES])
search = st.text_input("Search descriptions or merchants")
if from_date > to_date:
    st.error("The start date must be on or before the end date.")
    rows = []
else:
    rows = get_transactions(from_date.isoformat(), to_date.isoformat(),
                            type_filter, category_filter)
if search:
    query = search.casefold()
    rows = [row for row in rows if query in row["description"].casefold()
            or query in row["merchant"].casefold() or query in row["category"].casefold()]
sort_order = st.selectbox("Sort by", ["Newest first", "Oldest first", "Amount: high to low",
                                      "Amount: low to high"])
if sort_order == "Oldest first":
    rows.sort(key=lambda row: (row["transaction_date"], row["id"]))
elif sort_order == "Amount: high to low":
    rows.sort(key=lambda row: (-row["amount_paise"], row["transaction_date"]))
elif sort_order == "Amount: low to high":
    rows.sort(key=lambda row: (row["amount_paise"], row["transaction_date"]))
page_size = st.selectbox("Rows per page", [10, 25, 50])
page_count = max((len(rows) + page_size - 1) // page_size, 1)
page_number = st.number_input("Page", min_value=1, max_value=page_count, value=1)
visible_rows = rows[(page_number - 1) * page_size:page_number * page_size]
if rows:
    df = pd.DataFrame([{
        "ID": row["id"], "Date": row["transaction_date"], "Type": row["transaction_type"],
        "Category": row["category"], "Description": row["description"],
        "Merchant": row["merchant"], "Payment": row["payment_method"],
        "Amount (₹)": row["amount_paise"] / 100,
    } for row in visible_rows])
    st.dataframe(df, width="stretch", hide_index=True)
else:
    st.info("No transactions match these filters.")

if rows:
    st.divider()
    st.subheader("Edit or delete")
    selected_id = st.selectbox("Choose transaction ID", [row["id"] for row in rows])
    selected = get_transaction(selected_id)
    if selected:
        with st.form("edit_transaction"):
            c1, c2, c3 = st.columns(3)
            new_date = c1.date_input("Date", value=date.fromisoformat(selected["transaction_date"]),
                                     key="edit_date")
            new_type = c2.selectbox("Type", TRANSACTION_TYPES,
                                    index=TRANSACTION_TYPES.index(selected["transaction_type"]),
                                    key="edit_type")
            new_amount = c3.number_input("Amount (₹)", min_value=0.01,
                value=selected["amount_paise"] / 100, step=50.0, format="%.2f", key="edit_amount")
            category_options = (CATEGORIES if selected["category"] in CATEGORIES
                                else [selected["category"], *CATEGORIES])
            payment_options = (PAYMENT_METHODS if selected["payment_method"] in PAYMENT_METHODS
                               else [selected["payment_method"], *PAYMENT_METHODS])
            new_category = c1.selectbox("Category", category_options,
                index=category_options.index(selected["category"]), key="edit_category")
            new_payment = c2.selectbox("Payment method", payment_options,
                index=payment_options.index(selected["payment_method"]), key="edit_payment")
            new_merchant = c3.text_input("Merchant", value=selected["merchant"], key="edit_merchant")
            new_description = st.text_input("Description", value=selected["description"],
                                            key="edit_description")
            save = st.form_submit_button("Update transaction")
        if save:
            try:
                update_transaction(selected_id, new_date.isoformat(), new_type, new_amount,
                                  new_category, new_description, new_payment, new_merchant)
                st.success("Transaction updated.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
            except Exception:
                st.error("Could not update this transaction. Check the local database and try again.")
        if st.checkbox(f"I understand transaction {selected_id} will be permanently deleted.",
                       key=f"confirm_delete_{selected_id}"):
            if st.button("Delete transaction", type="secondary"):
                try:
                    delete_transaction(selected_id)
                    st.success("Transaction deleted.")
                    st.rerun()
                except Exception:
                    st.error("Could not delete this transaction. Check the local database and try again.")
