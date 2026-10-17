# FinWise AI — Smart Expense & Budget Coach

FinWise AI is a local-first personal finance dashboard for recording transactions, tracking category budgets and savings goals, scanning receipts, and exploring data-grounded spending insights. It is built as a beginner-friendly college project using Python, Streamlit, and SQLite.

> This is a local, single-user demonstration—not a production-grade, multi-user financial platform or regulated financial advice service. Net cash flow is income minus recorded expenses; it is not an account balance or confirmed savings.

## Problem statement

Personal spending is easy to lose track of across categories and months. FinWise AI provides one local place to record income and expenses, compare them against budgets, and review trends using deterministic calculations. Optional Gemini explanations receive summarized financial data only when the user requests AI insights.

## Objectives and features

- Record, search, filter, sort, edit, and delete income and expenses.
- Store monetary amounts in integer paise in SQLite.
- Review monthly income, expenses, net cash flow, spending categories, trends, and budget usage.
- Set monthly category limits and see calculated warnings for nearing or exceeded budgets.
- Create savings goals, enter actual progress, and view estimated contribution amounts.
- Ask Gemini questions about recorded transactions and computed summaries, with optional prior-month context and calculated percentage-reduction scenarios.
- Extract receipt text locally using Tesseract OCR, review editable suggestions, then explicitly confirm before saving.
- Export transaction CSVs and monthly PDF reports.
- Run core tests without Gemini credentials or external service calls.

## Technology stack

Python 3.10+, Streamlit, SQLite, Pandas, Plotly, Google GenAI Python SDK, Pillow, pytesseract/Tesseract OCR, python-dotenv, ReportLab, and pytest. Compatible dependency ranges are listed in [`requirements.txt`](requirements.txt).

## Architecture

```text
app.py                    Dashboard, navigation, and app startup
pages/                    Streamlit pages for transactions, budgets, AI,
                          receipt scanning, goals, reports, and settings
src/database.py           SQLite initialization, connection, and settings
src/transactions.py       Input validation and transaction CRUD
src/analytics.py          Deterministic monthly/category calculations
src/budget_service.py     Budget CRUD and utilization
src/goals.py              Savings goal tracking and estimates
src/ai_coach.py           Summarized context, Gemini calls, and scenarios
src/receipt_scanner.py    In-memory local OCR and conservative extraction
src/report_generator.py   CSV and PDF exports
tests/                    Automated service and validation tests
```

The database is created automatically at `data/finwise.db` on first run. Set `FINWISE_DB_PATH` to use a different local path. SQLite database files are ignored by Git. AI prompts contain calculated monthly/category/budget summaries rather than full transaction descriptions. Receipt processing uses the local Tesseract executable; uploaded images are not saved by the application.

## Screenshots

Add genuine screenshots of your running application here before publishing. No screenshots are included in this starter project.

## Installation and configuration

### Windows PowerShell

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks virtual-environment activation, use `.\.venv\Scripts\python.exe` instead of activating the environment.

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

### Gemini API key

The AI coach is optional. To enable it, obtain your own key from Google AI Studio and replace the placeholder `GEMINI_API_KEY` value in `.env`. Do not commit `.env`, share your key, or paste banking credentials into the coach. Without a key, transaction, budget, receipt, goal, and report features still work; the coach displays a configuration message.

When the coach runs, computed selected- and prior-month totals, category breakdowns, selected-month budget figures, and savings-goal totals/dates are sent to Google's Gemini API. Transaction descriptions and receipt images are not sent. Do not request or enter sensitive authentication information. AI responses are estimates and are not guaranteed financial outcomes or regulated financial advice.

### Receipt OCR setup

Install the Tesseract OCR application separately from the Python packages and ensure its executable is on `PATH`. Install a language data pack supported by your receipts (English is a common default). The scanner accepts JPG/JPEG and PNG images up to 5 MB, processes them in memory, and requires a user to review and confirm the extracted fields before saving. OCR may be inaccurate, especially for blurry or ambiguous receipts.

## Run the application

From the project directory, with the virtual environment active:

```powershell
streamlit run app.py
```

Open the local URL printed by Streamlit in your browser. Linux and macOS use the same command.

## Tests

```powershell
python -m pytest
```

The tests use temporary SQLite databases and do not require paid Gemini calls or a running OCR executable.

## Example AI questions

- Where did I spend the most this month?
- Suggest realistic ways I can reduce expenses.
- Create a budget plan for next month.
- What happens if I reduce Food expenses by 15%?

The application calculates totals and supported percentage-reduction scenarios in Python. The AI explains the supplied figures and should not be treated as an arithmetic engine.

## Privacy and limitations

- Financial records are stored locally by default; there is no account system or cloud sync.
- The app is intended for one local user. It does not include authentication, encryption-at-rest, backups, or multi-user access controls.
- Gemini is an external service; only summarized financial data is sent for an AI request.
- OCR runs locally if the Tesseract application is installed; images are not permanently stored by FinWise AI.
- Receipt date, merchant, category, and line-item suggestions may be incomplete or wrong and must be checked by the user.
- Supported scenario calculations currently cover reducing an existing expense category by a percentage.
- Savings projections assume a steady contribution schedule and are estimates only.

## Future improvements

Potential extensions include recurring transaction support, configurable currencies, richer receipt total/date parsing, encrypted backups, accessibility and localization review, and additional deterministic what-if scenarios.

## License

This project is released under the MIT License; see [`LICENSE`](LICENSE).
