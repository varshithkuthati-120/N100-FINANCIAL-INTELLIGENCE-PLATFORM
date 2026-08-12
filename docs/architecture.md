# System Architecture

The Nifty 100 Financial Ratio Engine follows a linear batch-processing and API-driven architecture.

## 1. ETL Pipeline (`src/etl`)
Reads raw CSV/Excel files from `data/`, normalizes the data (handling missing values, standardizing dates and tickers), and validates it using strict data quality rules before loading into a SQLite database (`nifty100.db`).

## 2. Analytics Engine (`src/analytics`)
Runs batch scripts (e.g., `clustering.py`) against the SQLite database to compute advanced statistics, generate correlation heatmaps, run KMeans clustering, and produce portfolio-level statistics saved in the `reports/` and `output/` directories.

## 3. FastAPI Server (`src/api`)
Provides a RESTful interface over the SQLite database. It serves 16 endpoints to retrieve company data, run dynamic screening, and fetch aggregated sector or peer group statistics.

## 4. Streamlit Dashboard (`dashboard.py`)
A frontend web application that consumes the FastAPI endpoints to visualize the data interactively for end users.
