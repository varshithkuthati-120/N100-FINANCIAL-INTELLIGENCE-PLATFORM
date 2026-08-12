from fastapi import APIRouter, HTTPException
import sqlite3
import urllib.parse

router = APIRouter()
DB_PATH = 'nifty100.db'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.get("/companies/{ticker}/documents")
def get_company_documents(ticker: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT company_id FROM companies WHERE ticker = ?", (ticker,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
        
    query = """
    SELECT doc_type, doc_url, doc_date, description 
    FROM documents 
    WHERE company_id = ?
    """
    cursor.execute(query, (row['company_id'],))
    data = []
    for r in cursor.fetchall():
        d = dict(r)
        
        # Check if URL is valid (basic check)
        is_url_valid = False
        if d['doc_url']:
            parsed = urllib.parse.urlparse(d['doc_url'])
            if parsed.scheme in ('http', 'https') and bool(parsed.netloc):
                is_url_valid = True
                
        d['is_url_valid'] = is_url_valid
        data.append(d)
        
    conn.close()
    return data
