import os
import sqlite3
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_cagr(start_val, end_val, periods):
    if pd.isna(start_val) or pd.isna(end_val) or start_val <= 0 or end_val <= 0:
        return np.nan
    return ((end_val / start_val) ** (1/periods) - 1) * 100

def run_clustering(db_path='nifty100.db'):
    # Connect to the database
    conn = sqlite3.connect(db_path)
    
    # 1. Load Data
    companies = pd.read_sql("SELECT company_id, ticker, sector_id FROM companies", conn)
    sectors = pd.read_sql("SELECT sector_id, sector_name AS broad_sector FROM sectors", conn)
    companies = companies.merge(sectors, on='sector_id', how='left')
    
    pnl = pd.read_sql("SELECT company_id, year, sales, opm FROM profitandloss", conn)
    analysis = pd.read_sql("SELECT company_id, year, roe, debt_to_equity FROM analysis", conn)
    cf = pd.read_sql("SELECT company_id, year, cfo, capex FROM cashflow", conn)
    cf['fcf'] = cf['cfo'] - cf['capex']
    
    # Process each company
    data = []
    
    for _, comp in companies.iterrows():
        cid = comp['company_id']
        ticker = comp['ticker']
        broad_sector = comp['broad_sector']
        
        # Latest data
        c_pnl = pnl[pnl['company_id'] == cid].sort_values('year')
        c_an = analysis[analysis['company_id'] == cid].sort_values('year')
        c_cf = cf[cf['company_id'] == cid].sort_values('year')
        
        if c_an.empty or c_pnl.empty or c_cf.empty:
            continue
            
        latest_an = c_an.iloc[-1]
        latest_pnl = c_pnl.iloc[-1]
        latest_cf = c_cf.iloc[-1]
        
        # 5 year ago data for CAGR
        # We find the data from (latest_year - 5) or oldest available up to 5
        year_5yr_ago = latest_pnl['year'] - 5
        pnl_5yr = c_pnl[c_pnl['year'] <= year_5yr_ago]
        cf_5yr = c_cf[c_cf['year'] <= year_5yr_ago]
        
        # Revenue CAGR 5yr
        if not pnl_5yr.empty:
            sales_5yr = pnl_5yr.iloc[-1]['sales']
            sales_latest = latest_pnl['sales']
            revenue_cagr_5yr = calculate_cagr(sales_5yr, sales_latest, 5)
        else:
            revenue_cagr_5yr = np.nan
            
        # FCF CAGR 5yr
        if not cf_5yr.empty:
            fcf_5yr = cf_5yr.iloc[-1]['fcf']
            fcf_latest = latest_cf['fcf']
            fcf_cagr_5yr = calculate_cagr(fcf_5yr, fcf_latest, 5)
        else:
            fcf_cagr_5yr = np.nan
            
        data.append({
            'company_id': ticker,  # Using ticker as company_id for the output 
            'cid': cid,
            'broad_sector': broad_sector,
            'return_on_equity_pct': latest_an['roe'],
            'debt_to_equity': latest_an['debt_to_equity'],
            'operating_profit_margin_pct': latest_pnl['opm'],
            'revenue_cagr_5yr': revenue_cagr_5yr,
            'fcf_cagr_5yr': fcf_cagr_5yr
        })
        
    df = pd.DataFrame(data)
    
    # Fill in missing companies if any didn't have data
    all_tickers = pd.DataFrame({'company_id': companies['ticker'], 'cid': companies['company_id'], 'broad_sector': companies['broad_sector']})
    df = pd.merge(all_tickers, df.drop(columns=['broad_sector']), on=['company_id', 'cid'], how='left')
    
    features = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr', 'fcf_cagr_5yr', 'operating_profit_margin_pct']
    
    # Impute missing values with sector median for each metric
    for feature in features:
        df[feature] = df.groupby('broad_sector')[feature].transform(lambda x: x.fillna(x.median()))
        # If any sector entirely NaN, fill with overall median
        df[feature] = df[feature].fillna(df[feature].median())
        
    # Scale with StandardScaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[features])
    
    # Generate elbow plot (inertia vs k from 2 to 10)
    os.makedirs('reports', exist_ok=True)
    inertias = []
    K_range = range(2, 11)
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X_scaled)
        inertias.append(km.inertia_)
        
    plt.figure(figsize=(8, 5))
    plt.plot(K_range, inertias, marker='o')
    plt.title('Elbow Plot for KMeans Clustering')
    plt.xlabel('Number of clusters (k)')
    plt.ylabel('Inertia')
    plt.grid(True)
    plt.savefig('reports/elbow_plot.png')
    plt.close()
    
    # Run KMeans with n_clusters=5, random_state=42
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    df['cluster_id'] = kmeans.fit_predict(X_scaled)
    
    # Compute distance from centroid
    centroids = kmeans.cluster_centers_
    distances = np.linalg.norm(X_scaled - centroids[df['cluster_id']], axis=1)
    df['distance_from_centroid'] = distances
    
    # --- Day 37: Cluster Profiling & Statistics ---
    cluster_profiles = df.groupby('cluster_id')[features].mean()
    
    cluster_names = {}
    sorted_by_roe = cluster_profiles.sort_values('return_on_equity_pct', ascending=False).index.tolist()
    
    for c_id in range(5):
        if c_id == sorted_by_roe[0]:
            cluster_names[c_id] = 'High-Quality Compounders'
        elif c_id == sorted_by_roe[-1]:
            cluster_names[c_id] = 'Distressed or Turnaround'
            
    remaining_clusters = [c for c in range(5) if c not in cluster_names]
    highest_de = max(remaining_clusters, key=lambda c: cluster_profiles.loc[c, 'debt_to_equity'])
    cluster_names[highest_de] = 'Value Cyclicals'
    remaining_clusters.remove(highest_de)
    
    highest_rev_cagr = max(remaining_clusters, key=lambda c: cluster_profiles.loc[c, 'revenue_cagr_5yr'])
    cluster_names[highest_rev_cagr] = 'Emerging Growth'
    remaining_clusters.remove(highest_rev_cagr)
    
    cluster_names[remaining_clusters[0]] = 'Defensive Dividend Payers'
    df['cluster_name'] = df['cluster_id'].map(cluster_names)
    
    os.makedirs('output', exist_ok=True)
    df[['company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid']].to_csv('output/cluster_labels.csv', index=False)
    
    # 10 KPIs correlation
    fr = pd.read_sql("SELECT company_id, year, pe_ratio, pb_ratio, ev_ebitda, div_yield FROM financial_ratios", conn)
    an_ext = pd.read_sql("SELECT company_id, year, current_ratio, interest_cov FROM analysis", conn)
    
    latest_kpis = []
    for _, comp in companies.iterrows():
        cid = comp['company_id']
        ticker = comp['ticker']
        
        c_fr = fr[fr['company_id'] == cid].sort_values('year')
        c_an = an_ext[an_ext['company_id'] == cid].sort_values('year')
        
        pe = c_fr.iloc[-1]['pe_ratio'] if not c_fr.empty else np.nan
        pb = c_fr.iloc[-1]['pb_ratio'] if not c_fr.empty else np.nan
        ev_ebitda = c_fr.iloc[-1]['ev_ebitda'] if not c_fr.empty else np.nan
        div_yield = c_fr.iloc[-1]['div_yield'] if not c_fr.empty else np.nan
        current_ratio = c_an.iloc[-1]['current_ratio'] if not c_an.empty else np.nan
        
        latest_kpis.append({
            'company_id': ticker,
            'pe_ratio': pe,
            'pb_ratio': pb,
            'ev_ebitda': ev_ebitda,
            'div_yield': div_yield,
            'current_ratio': current_ratio
        })
        
    df_ext = pd.DataFrame(latest_kpis)
    df_all_kpis = pd.merge(df, df_ext, on='company_id', how='left')
    
    ten_kpis = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr', 'fcf_cagr_5yr', 'operating_profit_margin_pct',
                'pe_ratio', 'pb_ratio', 'ev_ebitda', 'div_yield', 'current_ratio']
                
    plt.figure(figsize=(10, 8))
    corr = df_all_kpis[ten_kpis].corr()
    sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f")
    plt.title("Pearson Correlation of 10 KPIs")
    plt.tight_layout()
    plt.savefig('reports/correlation_heatmap.png')
    plt.close()
    
    outliers = []
    for sector in df_all_kpis['broad_sector'].unique():
        sector_df = df_all_kpis[df_all_kpis['broad_sector'] == sector].copy()
        
        for kpi in ten_kpis:
            mean = sector_df[kpi].mean()
            std = sector_df[kpi].std()
            if std > 0:
                z_scores = (sector_df[kpi] - mean) / std
                outlier_mask = np.abs(z_scores) > 3
                for idx, row in sector_df[outlier_mask].iterrows():
                    outliers.append({
                        'company_id': row['company_id'],
                        'broad_sector': sector,
                        'kpi': kpi,
                        'value': row[kpi],
                        'z_score': z_scores[idx]
                    })
                    
    pd.DataFrame(outliers).to_csv('output/outlier_report.csv', index=False)
    
    stats = []
    for kpi in ten_kpis:
        s = df_all_kpis[kpi].dropna()
        stats.append({
            'KPI': kpi,
            'P10': np.percentile(s, 10) if not s.empty else np.nan,
            'P25': np.percentile(s, 25) if not s.empty else np.nan,
            'P50': np.percentile(s, 50) if not s.empty else np.nan,
            'P75': np.percentile(s, 75) if not s.empty else np.nan,
            'P90': np.percentile(s, 90) if not s.empty else np.nan,
            'Mean': s.mean(),
            'Std': s.std()
        })
    pd.DataFrame(stats).to_csv('output/portfolio_stats.csv', index=False)
    print("Clustering and Profiling Complete.")

if __name__ == '__main__':
    run_clustering()
