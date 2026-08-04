import pandas as pd
import re
import os
import sqlite3

def parse_analysis_text(input_path='data/raw/analysis.xlsx', output_path='output/analysis_parsed.csv', fail_path='output/parse_failures.csv', db_path='nifty100.db'):
    df = pd.read_excel(input_path)
    pattern = re.compile(r'(\d+)\s*Years?:?\s*([\d.]+)%')
    
    target_fields = ['compounded_sales_growth', 'compounded_profit_growth', 'stock_price_cagr', 'roe']
    
    parsed_data = []
    failures = []
    
    for _, row in df.iterrows():
        company_id = row.get('company_id') or row.get('ticker')
        for field in target_fields:
            if field in row and isinstance(row[field], str):
                text = row[field]
                match = pattern.search(text)
                if match:
                    period = int(match.group(1))
                    value = float(match.group(2))
                    parsed_data.append({
                        'company_id': company_id,
                        'metric_type': field,
                        'period_years': period,
                        'value_pct': value
                    })
                else:
                    failures.append({
                        'company_id': company_id,
                        'metric_type': field,
                        'text': text
                    })
                    
    parsed_df = pd.DataFrame(parsed_data, columns=['company_id', 'metric_type', 'period_years', 'value_pct'])
    fail_df = pd.DataFrame(failures, columns=['company_id', 'metric_type', 'text'])
    
    parsed_df.to_csv(output_path, index=False)
    fail_df.to_csv(fail_path, index=False)
    print(f"Parsed {len(parsed_df)} records. {len(fail_df)} failures.")
    
    # Cross validation if possible
    # We would read from db and compare
    if os.path.exists(db_path) and len(parsed_df) > 0:
        pass # To be implemented based on exact DB tables for CAGR

if __name__ == '__main__':
    parse_analysis_text()
