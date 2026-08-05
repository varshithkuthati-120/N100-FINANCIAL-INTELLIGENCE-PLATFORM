import pandas as pd
import sqlite3
import numpy as np

def generate_pros_cons(db_path='nifty100.db', output_path='output/pros_cons_generated.csv'):
    conn = sqlite3.connect(db_path)
    
    # Load data
    analysis = pd.read_sql("SELECT * FROM analysis", conn)
    cashflow = pd.read_sql("SELECT * FROM cashflow", conn)
    pnl = pd.read_sql("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql("SELECT * FROM balancesheet", conn)
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    companies = pd.read_sql("SELECT company_id, ticker, sector_id FROM companies", conn)
    sectors = pd.read_sql("SELECT sector_id, sector_name FROM sectors", conn)
    
    companies = companies.merge(sectors, on='sector_id', how='left')
    
    # FCF = cfo - capex (if capex is available, otherwise cfo + cfi?) 
    # Usually FCF = CFO - CapEx. Let's assume FCF = cfo - capex
    cashflow['fcf'] = cashflow['cfo'] - cashflow['capex']
    
    # EBITDA approx = op_profit (or pbt + interest + dep_amort)
    pnl['ebitda'] = pnl['pbt'] + pnl['interest'] + pnl['dep_amort']
    
    # Net Debt = total_debt - cash_equiv (if available, otherwise borrowings - cash_equiv)
    bs['net_debt'] = bs['total_debt'] - bs.get('cash_equiv', 0)
    
    results = []
    
    for _, comp in companies.iterrows():
        cid = comp['company_id']
        ticker = comp['ticker']
        is_financial = 'Financial' in str(comp['sector_name'])
        
        c_analysis = analysis[analysis['company_id'] == cid].sort_values('year')
        c_cf = cashflow[cashflow['company_id'] == cid].sort_values('year')
        c_pnl = pnl[pnl['company_id'] == cid].sort_values('year')
        c_bs = bs[bs['company_id'] == cid].sort_values('year')
        c_ratios = ratios[ratios['company_id'] == cid].sort_values('year')
        
        if len(c_analysis) == 0 or len(c_cf) == 0 or len(c_pnl) == 0 or len(c_bs) == 0:
            continue
            
        latest_analysis = c_analysis.iloc[-1]
        latest_cf = c_cf.iloc[-1]
        latest_pnl = c_pnl.iloc[-1]
        latest_bs = c_bs.iloc[-1]
        latest_ratios = c_ratios.iloc[-1] if len(c_ratios) > 0 else pd.Series()

        def add_pro(rule_id, text, conf=80):
            if conf > 60: results.append({'company_id': ticker, 'type': 'pro', 'rule_id': rule_id, 'text': text, 'confidence_pct': conf})
            
        def add_con(rule_id, text, conf=80):
            if conf > 60: results.append({'company_id': ticker, 'type': 'con', 'rule_id': rule_id, 'text': text, 'confidence_pct': conf})
            
        def get_cagr(series, years=5):
            if len(series) < years + 1: return 0
            val_first = series.iloc[-(years+1)]
            val_last = series.iloc[-1]
            if val_first <= 0: return 0
            return ((val_last / val_first) ** (1/years) - 1) * 100

        # Pro 1
        if len(c_analysis) >= 3 and (c_analysis['roe'].tail(3) > 20).all():
            add_pro('P1', "Consistently high return on equity above 20% demonstrates exceptional capital efficiency", 90)
            
        # Pro 2
        if len(c_cf) >= 5 and (c_cf['fcf'].tail(5) > 0).all():
            add_pro('P2', "Strong free cash flow generation over 5 years signals healthy business fundamentals", 85)
            
        # Pro 3
        if latest_analysis.get('debt_to_equity', 1) == 0 or latest_bs.get('total_debt', 1) == 0:
            add_pro('P3', "Debt-free balance sheet provides financial flexibility and eliminates interest burden", 95)
            
        # Pro 4
        rev_cagr = get_cagr(c_pnl['sales'], 5)
        if rev_cagr > 15:
            add_pro('P4', "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum", 80)
            
        # Pro 5
        if latest_pnl.get('opm', 0) > 25:
            add_pro('P5', "Operating profit margin above 25% indicates strong pricing power and cost discipline", 85)
            
        # Pro 6
        pat_cagr = get_cagr(c_pnl['net_profit'], 5)
        if pat_cagr > 20:
            add_pro('P6', "Net profit compounding at above 20% over 5 years creates significant shareholder value", 90)
            
        # Pro 7
        if latest_analysis.get('interest_cov', 0) > 10 or latest_analysis.get('debt_to_equity', 1) == 0:
            add_pro('P7', "Very high interest coverage ratio reflects negligible financial stress from debt servicing", 85)
            
        # Pro 8
        if latest_ratios.get('div_yield', 0) > 2 and latest_cf.get('fcf', 0) > 0:
            add_pro('P8', "Consistent dividend yield above 2% backed by positive free cash flow", 80)
            
        # Pro 9
        eps_cagr = get_cagr(c_pnl['eps'], 5)
        if eps_cagr > 15:
            add_pro('P9', "Earnings per share growing above 15% CAGR indicates strong earnings quality and compounding", 85)
            
        # Pro 10
        if len(c_analysis) >= 3:
            roes = c_analysis['roe'].tail(3).values
            if roes[2] > roes[1] > roes[0]:
                add_pro('P10', "Return on equity improving for 3 consecutive years shows strengthening business quality", 80)
                
        # Pro 11
        if 0 < rev_cagr < pat_cagr:
            add_pro('P11', "Revenue growing slower than profits shows improving operating leverage and scale benefits", 75)
            
        # Pro 12
        if len(c_bs) >= 2:
            assets_growing = c_bs['total_assets'].iloc[-1] > c_bs['total_assets'].iloc[-2]
            debt_declining = c_bs['total_debt'].iloc[-1] < c_bs['total_debt'].iloc[-2]
            if assets_growing and debt_declining:
                add_pro('P12', "Growing asset base funded by internal accruals reflects self-sustaining growth", 85)

        # Con 1
        de = latest_analysis.get('debt_to_equity', 0)
        if not is_financial and de > 2.0:
            add_con('C1', f"Debt-to-equity ratio of {de:.1f} is elevated for a non-financial company and warrants monitoring", 90)
            
        # Con 2
        if len(c_cf) >= 3 and (c_cf['fcf'].tail(3) < 0).all():
            add_con('C2', "Free cash flow negative for 3 consecutive years raises concern about cash generation quality", 85)
            
        # Con 3
        if len(c_pnl) >= 3:
            opms = c_pnl['opm'].tail(3).values
            if opms[2] < opms[1] < opms[0]:
                add_con('C3', "Operating margins declining for 3 consecutive years suggest pricing or cost pressure", 80)
                
        # Con 4
        if latest_pnl.get('net_profit', 0) < 0:
            add_con('C4', "Company reported a net loss in the most recent financial year", 95)
            
        # Con 5
        if len(c_pnl) >= 2:
            sales = c_pnl['sales'].tail(2).values
            if sales[1] < sales[0]:
                add_con('C5', "Revenue contraction over consecutive years indicates demand weakness or market share loss", 80)
                
        # Con 6
        icr = latest_analysis.get('interest_cov', 100)
        if icr < 1.5 and icr > 0:
            add_con('C6', "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations", 90)
            
        # Con 7
        div_payout = latest_pnl.get('dividend_payout', 0)
        if div_payout > 100:
            add_con('C7', "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable", 85)
            
        # Con 8
        if len(c_analysis) >= 3:
            des = c_analysis['debt_to_equity'].tail(3).values
            if des[2] > des[1] > des[0]:
                add_con('C8', "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk", 80)
                
        # Con 9
        if len(c_pnl) >= 3:
            epss = c_pnl['eps'].tail(3).values
            if epss[2] < epss[1] < epss[0]:
                add_con('C9', "Earnings per share declining for 3 consecutive years reflects deteriorating profitability", 85)
                
        # Con 10
        if latest_analysis.get('roce', 100) < 10:
            add_con('C10', "Return on capital employed below 10% suggests the business is not generating sufficient returns on invested capital", 80)
            
        # Con 11
        net_debt = latest_bs.get('net_debt', 0)
        ebitda = latest_pnl.get('ebitda', 1)
        if ebitda > 0 and (net_debt / ebitda) > 3:
            add_con('C11', "Net debt exceeding 3 times EBITDA is a high leverage ratio and limits financial flexibility", 85)
            
        # Con 12
        if rev_cagr > 0 and rev_cagr < 5:
            add_con('C12', "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum", 75)
            
    # Guarantee at least 1 pro and 1 con per company if missed
    results_df = pd.DataFrame(results, columns=['company_id', 'type', 'rule_id', 'text', 'confidence_pct'])
    
    # Ensure every company has 1 pro and 1 con
    for ticker in companies['ticker'].unique():
        company_res = results_df[results_df['company_id'] == ticker]
        if not (company_res['type'] == 'pro').any():
            results.append({'company_id': ticker, 'type': 'pro', 'rule_id': 'P0', 'text': 'Company maintains stable market position in its industry', 'confidence_pct': 65})
        if not (company_res['type'] == 'con').any():
            results.append({'company_id': ticker, 'type': 'con', 'rule_id': 'C0', 'text': 'Industry faces macroeconomic headwinds and regulatory risks', 'confidence_pct': 65})
            
    final_df = pd.DataFrame(results, columns=['company_id', 'type', 'rule_id', 'text', 'confidence_pct'])
    final_df.to_csv(output_path, index=False)
    print(f"Generated {len(final_df)} pros and cons.")

if __name__ == '__main__':
    generate_pros_cons()
