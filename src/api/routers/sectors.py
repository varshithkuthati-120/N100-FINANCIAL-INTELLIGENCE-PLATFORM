from fastapi import APIRouter, HTTPException
import sqlite3
import statistics

router = APIRouter()
DB_PATH = 'nifty100.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/sectors")
def get_sectors():
    conn = get_db()
    
    # We need all sectors with company_count, median_roe, median_pe, median_de
    # First, get all sectors and their companies
    query = """
    SELECT s.sector_name, c.company_id,
           (SELECT roe FROM analysis WHERE company_id = c.company_id ORDER BY year DESC LIMIT 1) as roe,
           (SELECT debt_to_equity FROM analysis WHERE company_id = c.company_id ORDER BY year DESC LIMIT 1) as de,
           (SELECT pe_ratio FROM financial_ratios WHERE company_id = c.company_id ORDER BY year DESC LIMIT 1) as pe
    FROM sectors s
    JOIN companies c ON s.sector_id = c.sector_id
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    sector_data = {}
    for row in rows:
        sn = row['sector_name']
        if sn not in sector_data:
            sector_data[sn] = {'count': 0, 'roe': [], 'pe': [], 'de': []}
            
        sector_data[sn]['count'] += 1
        if row['roe'] is not None: sector_data[sn]['roe'].append(row['roe'])
        if row['pe'] is not None: sector_data[sn]['pe'].append(row['pe'])
        if row['de'] is not None: sector_data[sn]['de'].append(row['de'])
        
    results = []
    for sn, metrics in sector_data.items():
        results.append({
            "sector": sn,
            "company_count": metrics['count'],
            "median_roe": statistics.median(metrics['roe']) if metrics['roe'] else None,
            "median_pe": statistics.median(metrics['pe']) if metrics['pe'] else None,
            "median_de": statistics.median(metrics['de']) if metrics['de'] else None,
        })
        
    return results

@router.get("/sectors/{sector}/companies")
def get_sector_companies(sector: str):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if sector exists
    cursor.execute("SELECT sector_id FROM sectors WHERE sector_name = ?", (sector,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Sector not found")
        
    query = """
    SELECT c.company_id, c.ticker, c.company_name, c.market_cap_cr,
           a.roe, a.debt_to_equity, a.roce
    FROM companies c
    JOIN sectors s ON c.sector_id = s.sector_id
    LEFT JOIN analysis a ON c.company_id = a.company_id 
                         AND a.year = (SELECT MAX(year) FROM analysis WHERE company_id = c.company_id)
    WHERE s.sector_name = ?
    """
    cursor.execute(query, (sector,))
    data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return data
