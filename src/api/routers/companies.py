from fastapi import APIRouter, HTTPException, Query
import sqlite3
from typing import Optional, List
from fastapi.responses import FileResponse
import os

router = APIRouter()
DB_PATH = 'nifty100.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/companies")
def get_companies(
    sector: Optional[str] = None,
    market_cap_category: Optional[str] = None,
    search: Optional[str] = None
):
    conn = get_db()
    
    # We need: id, company_name, broad_sector, sub_sector, roe_pct, roce_pct
    query = """
    SELECT c.company_id as id, c.ticker, c.company_name, s.sector_name as broad_sector, 
           c.market_cap_cr,
           (SELECT a.roe FROM analysis a WHERE a.company_id = c.company_id ORDER BY year DESC LIMIT 1) as roe_pct,
           (SELECT a.roce FROM analysis a WHERE a.company_id = c.company_id ORDER BY year DESC LIMIT 1) as roce_pct
    FROM companies c
    JOIN sectors s ON c.sector_id = s.sector_id
    WHERE 1=1
    """
    params = []
    
    if sector:
        query += " AND s.sector_name = ?"
        params.append(sector)
    
    if search:
        query += " AND (c.company_name LIKE ? OR c.ticker LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        r = dict(row)
        r['sub_sector'] = r['broad_sector'] # no sub_sector in schema
        
        # apply market cap category filter in Python if needed
        mc = r['market_cap_cr']
        cat = "Unknown"
        if mc:
            if mc >= 50000: cat = "Large Cap"
            elif mc >= 10000: cat = "Mid Cap"
            else: cat = "Small Cap"
            
        r['market_cap_category'] = cat
        
        if market_cap_category and cat.lower() != market_cap_category.lower():
            continue
            
        results.append(r)
        
    conn.close()
    return results

@router.get("/companies/{ticker}")
def get_company_profile(ticker: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, s.sector_name 
        FROM companies c 
        JOIN sectors s ON c.sector_id = s.sector_id 
        WHERE c.ticker = ?
    """, (ticker,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
        
    comp = dict(row)
    
    # Get latest KPIs
    cursor.execute("""
        SELECT * FROM analysis WHERE company_id = ? ORDER BY year DESC LIMIT 1
    """, (comp['company_id'],))
    kpi_row = cursor.fetchone()
    if kpi_row:
        comp['latest_kpis'] = dict(kpi_row)
    else:
        comp['latest_kpis'] = None
        
    conn.close()
    return comp

@router.get("/companies/{ticker}/pl")
def get_company_pl(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [row['company_id']]
    
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
        
    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data

@router.get("/companies/{ticker}/bs")
def get_company_bs(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [row['company_id']]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data

@router.get("/companies/{ticker}/cashflow")
def get_company_cf(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [row['company_id']]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"
    cursor.execute(query, params)
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return data

@router.get("/companies/{ticker}/ratios")
def get_company_ratios(ticker: str, year: Optional[int] = None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
        
    # Join analysis and financial_ratios
    query = """
    SELECT a.*, f.pe_ratio, f.pb_ratio, f.ps_ratio, f.ev_ebitda, f.div_yield, f.beta, f.sharpe
    FROM analysis a
    LEFT JOIN financial_ratios f ON a.company_id = f.company_id AND a.year = f.year
    WHERE a.company_id = ?
    """
    params = [row['company_id']]
    if year:
        query += " AND a.year = ?"
        params.append(year)
    query += " ORDER BY a.year ASC"
    cursor.execute(query, params)
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    if year and len(data) == 1:
        return data[0]
    return data

@router.get("/companies/{ticker}/tearsheet")
def get_company_tearsheet(ticker: str):
    # Check reports/tearsheets
    # Wait, earlier I noted there is Sprint5_Deliverables/reports/tearsheets
    # Try multiple possible paths
    paths = [
        f"reports/tearsheets/{ticker}_tearsheet.pdf",
        f"Sprint5_Deliverables/reports/tearsheets/{ticker}_tearsheet.pdf"
    ]
    
    for path in paths:
        if os.path.exists(path):
            return FileResponse(path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf")
            
    raise HTTPException(status_code=404, detail="Tearsheet not found")
