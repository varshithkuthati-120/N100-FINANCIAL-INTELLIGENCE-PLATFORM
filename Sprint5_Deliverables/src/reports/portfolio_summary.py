import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def get_trend(current, previous):
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return ""
    diff_pct = (current - previous) / abs(previous)
    if diff_pct > 0.02: return "↑"
    elif diff_pct < -0.02: return "↓"
    else: return "→"

def generate_portfolio_summary():
    conn = sqlite3.connect('nifty100.db')
    companies = pd.read_sql("SELECT company_id, ticker, company_name, sector_id FROM companies", conn)
    sectors = pd.read_sql("SELECT sector_id, sector_name FROM sectors", conn)
    companies = companies.merge(sectors, on='sector_id', how='left').sort_values('ticker')
    
    pnl = pd.read_sql("SELECT * FROM profitandloss", conn)
    analysis = pd.read_sql("SELECT * FROM analysis", conn)
    
    out_path = 'reports/portfolio/portfolio_summary.pdf'
    doc = SimpleDocTemplate(out_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', fontSize=18, textColor=colors.white, backColor=colors.navy, alignment=1, spaceAfter=10, padding=10)
    
    elements = []
    
    for _, comp in companies.iterrows():
        cid = comp['company_id']
        ticker = comp['ticker']
        c_name = comp['company_name']
        s_name = comp['sector_name']
        
        c_pnl = pnl[pnl['company_id'] == cid].sort_values('year')
        c_analysis = analysis[analysis['company_id'] == cid].sort_values('year')
        
        if len(c_pnl) < 2 or len(c_analysis) < 2:
            continue
            
        cur_pnl = c_pnl.iloc[-1]
        prev_pnl = c_pnl.iloc[-2]
        cur_analysis = c_analysis.iloc[-1]
        prev_analysis = c_analysis.iloc[-2]
        
        elements.append(Paragraph(f"<b>{c_name} ({ticker})</b>", title_style))
        elements.append(Paragraph(f"<b>Sector:</b> {s_name}", styles['Heading3']))
        elements.append(Spacer(1, 20))
        
        kpis = [
            ("Revenue", cur_pnl.get('sales', 0), prev_pnl.get('sales', 0)),
            ("Net Profit", cur_pnl.get('net_profit', 0), prev_pnl.get('net_profit', 0)),
            ("OPM", cur_pnl.get('opm', 0), prev_pnl.get('opm', 0)),
            ("ROE", cur_analysis.get('roe', 0), prev_analysis.get('roe', 0)),
            ("ROCE", cur_analysis.get('roce', 0), prev_analysis.get('roce', 0)),
            ("D/E", cur_analysis.get('debt_to_equity', 0), prev_analysis.get('debt_to_equity', 0)) # Note lower is better for D/E but arrow is absolute
        ]
        
        data = [["Metric", "Current Value", "Trend"]]
        for name, cur, prev in kpis:
            trend = get_trend(cur, prev)
            # For D/E, an increase is technically bad, but we just show direction. Let's make it standard.
            if name in ['OPM', 'ROE', 'ROCE']: cur_str = f"{cur:.1f}%"
            elif name in ['Revenue', 'Net Profit']: cur_str = f"Rs. {cur:.1f} Cr"
            else: cur_str = f"{cur:.2f}"
            data.append([name, cur_str, trend])
            
        t = Table(data, colWidths=[2*72, 2*72, 1*72])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.navy),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        
        elements.append(t)
        elements.append(PageBreak())
        
    doc.build(elements)
    print("Portfolio summary generated.")

if __name__ == '__main__':
    generate_portfolio_summary()
