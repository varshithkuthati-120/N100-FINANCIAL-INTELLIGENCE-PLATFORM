from fastapi import APIRouter, HTTPException
import sqlite3

router = APIRouter()
DB_PATH = 'nifty100.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/market-cap/{ticker}")
def get_historical_valuation(ticker: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # from 2019 to 2024
    query = """
    SELECT year, pe_ratio, pb_ratio, ev_ebitda, div_yield 
    FROM financial_ratios 
    WHERE company_id = ? AND year BETWEEN 2019 AND 2024
    ORDER BY year ASC
    """
    cursor.execute(query, (row['company_id'],))
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data
