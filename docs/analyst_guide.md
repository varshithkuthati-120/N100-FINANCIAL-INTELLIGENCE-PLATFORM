# Analyst Guide - Nifty 100 Financial Ratio Engine

## Introduction
This engine provides an automated pipeline for calculating and serving over 10 KPIs across 92 companies in the Nifty 100 index. It aggregates 5 years of historical financial statements (Profit & Loss, Balance Sheet, Cash Flow) into a single SQLite database, performs advanced feature engineering and clustering, and exposes the data via a fast REST API.

## KPI Definitions
- **ROE (Return on Equity):** Net Income / Total Equity. Evaluates how effectively management uses shareholders' capital.
- **ROCE (Return on Capital Employed):** EBIT / (Total Assets - Current Liabilities). Evaluates overall capital efficiency.
- **Debt-to-Equity:** Total Debt / Total Equity. Measures financial leverage and risk.
- **Interest Coverage Ratio:** EBIT / Interest Expense. Indicates ability to service debt.
- **OPM (Operating Profit Margin):** Operating Profit / Revenue. Assesses core operational profitability.
- **Free Cash Flow (FCF):** Cash from Operations (CFO) - Capital Expenditures (CapEx). Represents discretionary cash available.
- **P/E Ratio:** Market Price / Earnings per Share. Indicates market valuation relative to earnings.
- **EV/EBITDA:** Enterprise Value / EBITDA. A capital-structure-neutral valuation metric.

## Using the API
Analysts can programmatically access the data through the FastAPI service at `http://localhost:8000/api/v1`. The `screener` endpoint is particularly useful for building custom investment strategies (e.g., screening for ROE > 15% and D/E < 1.0).

## Dashboard
A Streamlit dashboard is provided (`dashboard.py`) to visually explore the data, compare peer groups, and view detailed company tearsheets.
