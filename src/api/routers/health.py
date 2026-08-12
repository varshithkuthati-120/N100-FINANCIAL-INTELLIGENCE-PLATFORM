from fastapi import APIRouter
import sqlite3
import time

router = APIRouter()
START_TIME = time.time()
DB_PATH = 'nifty100.db'

TABLES = [
    'companies', 'sectors', 'profitandloss', 'balancesheet', 
    'cashflow', 'analysis', 'documents', 'prosandcons', 
    'stock_prices', 'financial_ratios'
]

@router.get("/health")
def get_health():
    db_row_counts = {}
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        for table in TABLES:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            db_row_counts[table] = cursor.fetchone()[0]
        conn.close()
    except Exception as e:
        db_row_counts = {"error": str(e)}
        
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "version": "1.0.0",
        "db_row_counts": db_row_counts
    }
