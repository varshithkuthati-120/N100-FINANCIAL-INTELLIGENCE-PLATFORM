import pandas as pd

def check_dq_rules(df):
    violations = []
    for idx, row in df.iterrows():
        # DQ01: Missing ROE
        if pd.isna(row.get('roe')):
            violations.append({'rule_id': 'DQ01', 'severity': 'MEDIUM'})
            
        # DQ02: Negative Equity
        if row.get('equity', 1) <= 0:
            violations.append({'rule_id': 'DQ02', 'severity': 'HIGH'})
            
        # DQ03: Sales <= 0
        if row.get('sales', 1) <= 0:
            violations.append({'rule_id': 'DQ03', 'severity': 'HIGH'})
            
        # DQ04: Assets < Liabilities
        if row.get('total_assets', 1) < row.get('total_liab', 0):
            violations.append({'rule_id': 'DQ04', 'severity': 'CRITICAL'})
            
        # DQ05: Missing CFO
        if pd.isna(row.get('cfo')):
            violations.append({'rule_id': 'DQ05', 'severity': 'MEDIUM'})
            
        # DQ06: D/E > 10
        if row.get('debt_to_equity', 0) > 10:
            violations.append({'rule_id': 'DQ06', 'severity': 'HIGH'})
            
        # DQ07: Current Ratio < 0.5
        if row.get('current_ratio', 1) < 0.5:
            violations.append({'rule_id': 'DQ07', 'severity': 'MEDIUM'})
            
        # DQ08: Negative Sales (Error)
        if row.get('sales', 1) < 0:
            violations.append({'rule_id': 'DQ08', 'severity': 'CRITICAL'})
            
        # DQ09: Interest Coverage < 0
        if row.get('interest_cov', 1) < 0:
            violations.append({'rule_id': 'DQ09', 'severity': 'HIGH'})
            
        # DQ10: Missing PE Ratio
        if pd.isna(row.get('pe_ratio')):
            violations.append({'rule_id': 'DQ10', 'severity': 'LOW'})
            
        # DQ11: Missing PB Ratio
        if pd.isna(row.get('pb_ratio')):
            violations.append({'rule_id': 'DQ11', 'severity': 'LOW'})
            
        # DQ12: Zero Assets
        if row.get('total_assets', 1) == 0:
            violations.append({'rule_id': 'DQ12', 'severity': 'CRITICAL'})
            
        # DQ13: OPM > 100%
        if row.get('opm', 0) > 100:
            violations.append({'rule_id': 'DQ13', 'severity': 'HIGH'})
            
        # DQ14: Negative Taxes
        if row.get('tax', 1) < 0:
            violations.append({'rule_id': 'DQ14', 'severity': 'MEDIUM'})
            
    return violations
