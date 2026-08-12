import sqlite3
import pandas as pd
from scipy.stats import percentileofscore

def generate_peer_percentiles():
    conn = sqlite3.connect('nifty100.db')
    
    # 1. Create table if not exists
    conn.execute('''
    CREATE TABLE IF NOT EXISTS peer_percentiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT,
        company_id INTEGER,
        metric TEXT,
        percentile_rank REAL
    )
    ''')
    conn.execute('DELETE FROM peer_percentiles')
    
    # 2. Get data
    query = """
    WITH latest_year AS (SELECT company_id, MAX(year) as max_year FROM profitandloss GROUP BY company_id)
    SELECT c.company_id, pg.group_name,
           a.roe, a.roce, a.debt_to_equity, a.net_margin,
           p.opm, f.pe_ratio, f.pb_ratio, f.ev_ebitda,
           cf.cfo - cf.capex as fcf, p.sales
    FROM companies c
    JOIN peer_groups pg ON c.company_id = pg.company_id
    JOIN latest_year ly ON c.company_id = ly.company_id
    LEFT JOIN analysis a ON a.company_id = c.company_id AND a.year = ly.max_year
    LEFT JOIN profitandloss p ON p.company_id = c.company_id AND p.year = ly.max_year
    LEFT JOIN financial_ratios f ON f.company_id = c.company_id AND f.year = ly.max_year
    LEFT JOIN cashflow cf ON cf.company_id = c.company_id AND cf.year = ly.max_year
    """
    df = pd.read_sql(query, conn)
    
    metrics = ['roe', 'roce', 'debt_to_equity', 'net_margin', 'opm', 'pe_ratio', 'pb_ratio', 'ev_ebitda', 'fcf', 'sales']
    
    records = []
    for group in df['group_name'].unique():
        gdf = df[df['group_name'] == group]
        for metric in metrics:
            valid_vals = gdf[metric].dropna()
            if valid_vals.empty:
                continue
            for _, row in gdf.iterrows():
                if pd.notna(row[metric]):
                    pct = percentileofscore(valid_vals, row[metric])
                    records.append({
                        'group_name': group,
                        'company_id': row['company_id'],
                        'metric': metric,
                        'percentile_rank': pct
                    })
                    
    pd.DataFrame(records).to_sql('peer_percentiles', conn, if_exists='append', index=False)
    conn.commit()
    conn.close()
    print("Populated peer_percentiles table.")

if __name__ == '__main__':
    generate_peer_percentiles()
