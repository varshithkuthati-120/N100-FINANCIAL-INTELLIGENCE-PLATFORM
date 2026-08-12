from fastapi import APIRouter, HTTPException, Query
import sqlite3
from typing import Optional

router = APIRouter()
DB_PATH = 'nifty100.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/screener")
def run_screener(
    min_roe: Optional[float] = None,
    max_de: Optional[float] = None,
    min_fcf: Optional[float] = None,
    sector: Optional[str] = None,
    min_rev_cagr_5yr: Optional[float] = None,
    min_pat_cagr_5yr: Optional[float] = None,
    max_pe: Optional[float] = None
):
    try:
        if min_roe is not None: float(min_roe)
        if max_de is not None: float(max_de)
        if min_fcf is not None: float(min_fcf)
        if min_rev_cagr_5yr is not None: float(min_rev_cagr_5yr)
        if min_pat_cagr_5yr is not None: float(min_pat_cagr_5yr)
        if max_pe is not None: float(max_pe)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid parameter value. Expected a number.")
        
    conn = get_db()
    
    query = """
    WITH latest_year AS (
        SELECT company_id, MAX(year) as max_year FROM profitandloss GROUP BY company_id
    )
    SELECT c.ticker, c.company_name, s.sector_name as sector,
           a.roe, a.debt_to_equity,
           cf.cfo - cf.capex as fcf,
           f.pe_ratio,
           
           -- 5yr CAGR approximations using the data if needed, or we can just fetch the data and compute
           p_latest.sales as rev_latest,
           (SELECT sales FROM profitandloss WHERE company_id = c.company_id AND year = ly.max_year - 5) as rev_5yr,
           
           p_latest.net_profit as pat_latest,
           (SELECT net_profit FROM profitandloss WHERE company_id = c.company_id AND year = ly.max_year - 5) as pat_5yr
           
    FROM companies c
    JOIN sectors s ON c.sector_id = s.sector_id
    JOIN latest_year ly ON c.company_id = ly.company_id
    LEFT JOIN analysis a ON a.company_id = c.company_id AND a.year = ly.max_year
    LEFT JOIN cashflow cf ON cf.company_id = c.company_id AND cf.year = ly.max_year
    LEFT JOIN profitandloss p_latest ON p_latest.company_id = c.company_id AND p_latest.year = ly.max_year
    LEFT JOIN financial_ratios f ON f.company_id = c.company_id AND f.year = ly.max_year
    WHERE 1=1
    """
    
    params = []
    
    if sector:
        query += " AND s.sector_name = ?"
        params.append(sector)
        
    if min_roe is not None:
        query += " AND a.roe >= ?"
        params.append(min_roe)
        
    if max_de is not None:
        query += " AND a.debt_to_equity <= ?"
        params.append(max_de)
        
    if min_fcf is not None:
        query += " AND (cf.cfo - cf.capex) >= ?"
        params.append(min_fcf)
        
    if max_pe is not None:
        query += " AND f.pe_ratio <= ?"
        params.append(max_pe)
        
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        r = dict(row)
        
        # Calculate CAGRs
        rev_cagr = None
        if r['rev_latest'] and r['rev_5yr'] and r['rev_5yr'] > 0 and r['rev_latest'] > 0:
            rev_cagr = ((r['rev_latest'] / r['rev_5yr']) ** (1/5) - 1) * 100
            
        pat_cagr = None
        if r['pat_latest'] and r['pat_5yr'] and r['pat_5yr'] > 0 and r['pat_latest'] > 0:
            pat_cagr = ((r['pat_latest'] / r['pat_5yr']) ** (1/5) - 1) * 100
            
        r['rev_cagr_5yr'] = rev_cagr
        r['pat_cagr_5yr'] = pat_cagr
        
        # Apply CAGR filters
        if min_rev_cagr_5yr is not None and (rev_cagr is None or rev_cagr < min_rev_cagr_5yr):
            continue
        if min_pat_cagr_5yr is not None and (pat_cagr is None or pat_cagr < min_pat_cagr_5yr):
            continue
            
        # Clean up intermediate keys
        del r['rev_latest']
        del r['rev_5yr']
        del r['pat_latest']
        del r['pat_5yr']
        
        results.append(r)
        
    conn.close()
    
    # rank by ROE descending as default
    results.sort(key=lambda x: x['roe'] if x['roe'] is not None else -9999, reverse=True)
    return results
