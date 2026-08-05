import os
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_charts(ticker, pnl, analysis, bs, cf):
    os.makedirs('output/temp_charts', exist_ok=True)
    
    # 1. 10-year Revenue and Net Profit bar chart
    fig, ax = plt.subplots(figsize=(6, 3))
    years = pnl['year'].astype(str)
    x = range(len(years))
    width = 0.35
    ax.bar([i - width/2 for i in x], pnl['sales'], width, label='Revenue', color='#1f77b4')
    ax.bar([i + width/2 for i in x], pnl['net_profit'], width, label='Net Profit', color='#2ca02c')
    ax.set_xticks(x)
    ax.set_xticklabels(years, rotation=45)
    ax.legend()
    ax.set_title('Revenue & Net Profit')
    plt.tight_layout()
    chart1_path = f'output/temp_charts/{ticker}_chart1.png'
    plt.savefig(chart1_path)
    plt.close()
    
    # 2. ROE and ROCE dual-axis line chart
    fig, ax1 = plt.subplots(figsize=(6, 3))
    years_a = analysis['year'].astype(str)
    ax1.plot(years_a, analysis['roe'], color='blue', marker='o', label='ROE')
    ax1.set_ylabel('ROE (%)', color='blue')
    ax2 = ax1.twinx()
    ax2.plot(years_a, analysis['roce'], color='red', marker='x', label='ROCE')
    ax2.set_ylabel('ROCE (%)', color='red')
    plt.title('ROE vs ROCE')
    plt.tight_layout()
    chart2_path = f'output/temp_charts/{ticker}_chart2.png'
    plt.savefig(chart2_path)
    plt.close()
    
    # 3. Balance Sheet stacked bar
    fig, ax = plt.subplots(figsize=(6, 3))
    years_bs = bs['year'].astype(str)
    ax.bar(years_bs, bs['equity'], label='Equity', color='#2ca02c')
    ax.bar(years_bs, bs['borrowings'], bottom=bs['equity'], label='Borrowings', color='#d62728')
    other_liab = bs['total_liab'] - bs['equity'] - bs['borrowings']
    ax.bar(years_bs, other_liab, bottom=bs['equity']+bs['borrowings'], label='Other Liab', color='#7f7f7f')
    ax.legend()
    ax.set_title('Balance Sheet Composition')
    plt.tight_layout()
    chart3_path = f'output/temp_charts/{ticker}_chart3.png'
    plt.savefig(chart3_path)
    plt.close()
    
    # 4. Cash Flow waterfall (simplified as bar chart)
    fig, ax = plt.subplots(figsize=(6, 3))
    latest_cf = cf.iloc[-1]
    cats = ['CFO', 'CFI', 'CFF', 'Net Cash']
    vals = [latest_cf['cfo'], latest_cf['cfi'], latest_cf['cff'], latest_cf['net_cash']]
    ax.bar(cats, vals, color=['blue', 'red', 'orange', 'green'])
    ax.set_title('Cash Flow (Latest Year)')
    plt.tight_layout()
    chart4_path = f'output/temp_charts/{ticker}_chart4.png'
    plt.savefig(chart4_path)
    plt.close()
    
    return chart1_path, chart2_path, chart3_path, chart4_path

def build_tearsheet(ticker, company_name, pnl, analysis, bs, cf, pros, cons, cap_alloc, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(name='TitleStyle', fontSize=18, textColor=colors.white, backColor=colors.navy, alignment=1, spaceAfter=20, padding=10)
    pro_style = ParagraphStyle(name='Pro', textColor=colors.green, fontSize=10, bulletIndent=10, leftIndent=20, spaceAfter=5)
    con_style = ParagraphStyle(name='Con', textColor=colors.red, fontSize=10, bulletIndent=10, leftIndent=20, spaceAfter=5)
    
    elements = []
    
    # Header
    elements.append(Paragraph(f"<b>{company_name} ({ticker})</b>", title_style))
    
    # 6 KPIs
    if len(pnl) > 0 and len(analysis) > 0:
        latest_pnl = pnl.iloc[-1]
        latest_analysis = analysis.iloc[-1]
        data = [
            ["Revenue", f"Rs. {latest_pnl.get('sales', 0):.1f} Cr", "Net Profit", f"Rs. {latest_pnl.get('net_profit', 0):.1f} Cr", "OPM", f"{latest_pnl.get('opm', 0):.1f}%"],
            ["ROE", f"{latest_analysis.get('roe', 0):.1f}%", "ROCE", f"{latest_analysis.get('roce', 0):.1f}%", "D/E", f"{latest_analysis.get('debt_to_equity', 0):.2f}"]
        ]
        t = Table(data, colWidths=[1*inch, 1.5*inch]*3)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 20))
        
    c1, c2, c3, c4 = generate_charts(ticker, pnl, analysis, bs, cf)
    
    # Page 1 charts
    data_charts1 = [[RLImage(c1, width=3*inch, height=2*inch), RLImage(c2, width=3*inch, height=2*inch)]]
    t_charts1 = Table(data_charts1)
    elements.append(t_charts1)
    
    elements.append(PageBreak())
    
    # Page 2 charts
    data_charts2 = [[RLImage(c3, width=3*inch, height=2*inch), RLImage(c4, width=3*inch, height=2*inch)]]
    t_charts2 = Table(data_charts2)
    elements.append(t_charts2)
    elements.append(Spacer(1, 20))
    
    # Badge
    elements.append(Paragraph(f"<b>Capital Allocation Pattern:</b> {cap_alloc}", styles['Heading3']))
    elements.append(Spacer(1, 10))
    
    # Pros
    elements.append(Paragraph("<b>Pros:</b>", styles['Heading4']))
    for p in pros:
        elements.append(Paragraph(f"• {p}", pro_style))
    elements.append(Spacer(1, 10))
    
    # Cons
    elements.append(Paragraph("<b>Cons:</b>", styles['Heading4']))
    for c in cons:
        elements.append(Paragraph(f"• {c}", con_style))
        
    doc.build(elements)

def generate_all_tearsheets():
    conn = sqlite3.connect('nifty100.db')
    companies = pd.read_sql("SELECT company_id, ticker, company_name FROM companies", conn)
    pnl = pd.read_sql("SELECT * FROM profitandloss", conn)
    analysis = pd.read_sql("SELECT * FROM analysis", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    cf = pd.read_sql("SELECT * FROM cashflow", conn)
    
    try:
        pros_cons = pd.read_csv('output/pros_cons_generated.csv')
    except:
        pros_cons = pd.DataFrame(columns=['company_id', 'type', 'text'])
        
    try:
        cap_alloc_df = pd.read_csv('output/capital_allocation.csv')
    except:
        cap_alloc_df = pd.DataFrame(columns=['company_id', 'pattern'])

    skipped = []
    
    for _, comp in companies.iterrows():
        cid = comp['company_id']
        ticker = comp['ticker']
        c_name = comp['company_name']
        
        c_pnl = pnl[pnl['company_id'] == cid]
        c_analysis = analysis[analysis['company_id'] == cid]
        c_bs = bs[bs['company_id'] == cid]
        c_cf = cf[cf['company_id'] == cid]
        
        if len(c_pnl) < 3 or len(c_analysis) < 3:
            skipped.append(ticker)
            continue
            
        c_pros = pros_cons[(pros_cons['company_id'] == ticker) & (pros_cons['type'] == 'pro')]['text'].tolist()
        c_cons = pros_cons[(pros_cons['company_id'] == ticker) & (pros_cons['type'] == 'con')]['text'].tolist()
        
        if len(cap_alloc_df) > 0:
            c_cap_allocs = cap_alloc_df[cap_alloc_df['company_id'] == ticker]
            cap_alloc = c_cap_allocs.iloc[-1]['pattern'] if len(c_cap_allocs) > 0 else 'Unknown'
        else:
            cap_alloc = 'Unknown'
            
        out_path = f'reports/tearsheets/{ticker}_tearsheet.pdf'
        build_tearsheet(ticker, c_name, c_pnl, c_analysis, c_bs, c_cf, c_pros, c_cons, cap_alloc, out_path)
        
    pd.DataFrame({'ticker': skipped}).to_csv('output/skipped_tearsheets.csv', index=False)
    print(f"Generated {len(companies) - len(skipped)} tearsheets. Skipped {len(skipped)}.")

if __name__ == '__main__':
    generate_all_tearsheets()
