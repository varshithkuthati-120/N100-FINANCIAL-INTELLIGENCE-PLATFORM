# Nifty 100 Financial Ratio Engine

## How to run the full pipeline from scratch
1. Initialize the database and run the ETL loader:
   ```bash
   python src/etl/loader.py
   ```
2. Generate clustering and portfolio stats:
   ```bash
   python src/analytics/clustering.py
   python scripts/create_peer_percentiles.py
   ```

## How to start API server
```bash
uvicorn src.api.main:app --port 8000
```

## How to run the Streamlit Dashboard
```bash
streamlit run dashboard.py
```

## How to run unit tests
```bash
python -m pytest tests/etl/ tests/kpi/ tests/dq/ tests/api/ -v
```
