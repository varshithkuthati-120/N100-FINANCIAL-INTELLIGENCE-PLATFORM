from fastapi import APIRouter, HTTPException
import sqlite3

router = APIRouter()
DB_PATH = 'nifty100.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/peers/{group_name}")
def get_peer_group(group_name: str):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if group exists
    cursor.execute("SELECT 1 FROM peer_groups WHERE group_name = ? LIMIT 1", (group_name,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Peer group not found")
        
    query = """
    SELECT c.ticker, c.company_name, pp.metric, pp.percentile_rank
    FROM peer_percentiles pp
    JOIN companies c ON c.company_id = pp.company_id
    WHERE pp.group_name = ?
    """
    cursor.execute(query, (group_name,))
    rows = cursor.fetchall()
    conn.close()
    
    # Group by company
    companies = {}
    for row in rows:
        t = row['ticker']
        if t not in companies:
            companies[t] = {
                "ticker": t,
                "company_name": row['company_name'],
                "metrics": {}
            }
        companies[t]["metrics"][row['metric']] = row['percentile_rank']
        
    return list(companies.values())

@router.get("/companies/{ticker}/peers/compare")
def get_company_peer_compare(ticker: str):
    conn = get_db()
    cursor = conn.cursor()
    
    # Get company and its peer group
    cursor.execute("""
        SELECT c.company_id, pg.group_name 
        FROM companies c 
        JOIN peer_groups pg ON c.company_id = pg.company_id
        WHERE c.ticker = ?
    """, (ticker,))
    row = cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Company or peer group not found")
        
    company_id = row['company_id']
    group_name = row['group_name']
    
    # We need 8 axis metric values for the company + peer group average + benchmark company
    metrics = ['roe', 'roce', 'debt_to_equity', 'net_margin', 'opm', 'pe_ratio', 'pb_ratio', 'ev_ebitda']
    
    # Get all latest year data for this peer group
    query = """
    WITH latest_year AS (SELECT company_id, MAX(year) as max_year FROM profitandloss GROUP BY company_id)
    SELECT c.company_id, c.ticker,
           a.roe, a.roce, a.debt_to_equity, a.net_margin,
           p.opm, f.pe_ratio, f.pb_ratio, f.ev_ebitda
    FROM companies c
    JOIN peer_groups pg ON c.company_id = pg.company_id
    JOIN latest_year ly ON c.company_id = ly.company_id
    LEFT JOIN analysis a ON a.company_id = c.company_id AND a.year = ly.max_year
    LEFT JOIN profitandloss p ON p.company_id = c.company_id AND p.year = ly.max_year
    LEFT JOIN financial_ratios f ON f.company_id = c.company_id AND f.year = ly.max_year
    WHERE pg.group_name = ?
    """
    cursor.execute(query, (group_name,))
    group_data = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    company_data = next((d for d in group_data if d['company_id'] == company_id), None)
    if not company_data:
        raise HTTPException(status_code=404, detail="Company data not found in peer group")
        
    # Calculate group average
    group_avg = {}
    for m in metrics:
        vals = [d[m] for d in group_data if d.get(m) is not None]
        group_avg[m] = sum(vals) / len(vals) if vals else None
        
    # Find benchmark company (highest market cap in peer group usually, but let's just pick the first one with max ROE for now)
    benchmark = max(group_data, key=lambda x: x.get('roe') or -9999)
    
    return {
        "company": {m: company_data.get(m) for m in metrics},
        "group_average": group_avg,
        "benchmark": {
            "ticker": benchmark['ticker'],
            "metrics": {m: benchmark.get(m) for m in metrics}
        }
    }
