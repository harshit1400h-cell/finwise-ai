import os

import streamlit as st
from dotenv import load_dotenv

from src.database import database_path, init_db

init_db()
load_dotenv()
st.title("⚙️ Settings")
st.caption("FinWise AI is designed for a local, single-user demonstration.")
st.subheader("Local storage")
st.write("Transactions, budgets, savings goals, and settings are stored in the local SQLite database.")
st.code(str(database_path()), language=None)
st.write("Display currency is Indian Rupees (₹) in this version.")
st.warning("Protect your device and database file. This project is not a production-grade multi-user financial platform.")
st.subheader("Gemini API")
st.write("AI requests send summarized financial data for the selected month to Google's Gemini API.")
if os.environ.get("GEMINI_API_KEY"):
    st.success("GEMINI_API_KEY is configured for this application.")
else:
    st.info("Gemini is not configured. Add GEMINI_API_KEY to your local .env file. No key is stored in the app database.")
st.subheader("Receipt OCR")
st.write("Receipt images are processed in memory using local Tesseract OCR and are not permanently stored.")
st.caption("Optional database override: FINWISE_DB_PATH.")
