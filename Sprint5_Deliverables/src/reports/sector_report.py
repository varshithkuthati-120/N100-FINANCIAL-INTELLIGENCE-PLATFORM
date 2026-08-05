import pandas as pd
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_sector_reports():
    conn = sqlite3.connect('nifty100.db')
    sectors = pd.read_sql("SELECT * FROM sectors", conn)
    companies = pd.read_sql("SELECT company_id, ticker, company_name, sector_id FROM companies", conn)
    pnl = pd.read_sql("SELECT * FROM profitandloss", conn)
    analysis = pd.read_sql("SELECT * FROM analysis", conn)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='TitleStyle', fontSize=18, textColor=colors.white, backColor=colors.navy, alignment=1, spaceAfter=20, padding=10)
    
    for _, sector in sectors.iterrows():
        sid = sector['sector_id']
        sname = sector['sector_name']
        s_comps = companies[companies['sector_id'] == sid]
        
        if len(s_comps) == 0:
            continue
            
        out_path = f'reports/sector/{sname.replace(" ", "_")}_report.pdf'
        doc = SimpleDocTemplate(out_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
        elements = []
        
        elements.append(Paragraph(f"<b>Sector Report: {sname}</b>", title_style))
        
        # Calculate medians
        cids = s_comps['company_id'].tolist()
        s_pnl = pnl[pnl['company_id'].isin(cids)].sort_values('year').groupby('company_id').last()
        s_analysis = analysis[analysis['company_id'].isin(cids)].sort_values('year').groupby('company_id').last()
        
        med_roe = s_analysis['roe'].median() if 'roe' in s_analysis else 0
        med_roce = s_analysis['roce'].median() if 'roce' in s_analysis else 0
        med_opm = s_pnl['opm'].median() if 'opm' in s_pnl else 0
        med_sales = s_pnl['sales'].median() if 'sales' in s_pnl else 0
        
        elements.append(Paragraph("<b>Sector Medians</b>", styles['Heading2']))
        med_data = [
            ["Median ROE", f"{med_roe:.1f}%", "Median ROCE", f"{med_roce:.1f}%"],
            ["Median OPM", f"{med_opm:.1f}%", "Median Sales", f"Rs. {med_sales:.1f} Cr"]
        ]
        t_med = Table(med_data, colWidths=[1.5*72, 1.5*72, 1.5*72, 1.5*72])
        t_med.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(t_med)
        elements.append(Spacer(1, 20))
        
        elements.append(Paragraph("<b>Companies in Sector</b>", styles['Heading2']))
        
        # 8 metrics for each company (Ticker, Name, Sales, OPM, Net Profit, ROE, ROCE, D/E)
        comp_data = [["Ticker", "Name", "Sales", "OPM", "Net Profit", "ROE", "ROCE", "D/E"]]
        for _, comp in s_comps.iterrows():
            cid2 = comp['company_id']
            try:
                cp = s_pnl.loc[cid2]
                ca = s_analysis.loc[cid2]
                comp_data.append([
                    comp['ticker'],
                    comp['company_name'][:15],
                    f"{cp.get('sales', 0):.0f}",
                    f"{cp.get('opm', 0):.1f}%",
                    f"{cp.get('net_profit', 0):.0f}",
                    f"{ca.get('roe', 0):.1f}%",
                    f"{ca.get('roce', 0):.1f}%",
                    f"{ca.get('debt_to_equity', 0):.1f}"
                ])
            except KeyError:
                continue
                
        t_comp = Table(comp_data)
        t_comp.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.navy),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(t_comp)
        
        doc.build(elements)
    print("Sector reports generated.")

if __name__ == '__main__':
    generate_sector_reports()
