"""
generate_sample_data.py
Generate 12 realistic Nifty 100 source Excel files (7 core + 5 supplementary).

Usage:
    python scripts/generate_sample_data.py

Output files in data/raw/:
    Core (7):
        1. sectors.xlsx
        2. companies.xlsx
        3. profitandloss.xlsx
        4. balancesheet.xlsx
        5. cashflow.xlsx
        6. stock_prices.xlsx
        7. financial_ratios.xlsx
    Supplementary (5):
        8. analysis.xlsx
        9. documents.xlsx
        10. prosandcons.xlsx
        11. peer_groups.xlsx
        12. sectors_supplementary.xlsx
"""

import os
import random
import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# ============================================================
# Reference data
# ============================================================

SECTORS = [
    "Oil & Gas", "Banking", "IT Services", "FMCG", "Automobile",
    "Pharma", "Cement", "Metals", "Power", "Financial Services",
    "Telecom", "Construction", "Consumer Durables", "Healthcare",
    "Logistics", "Chemicals", "Insurance", "Realty",
]

TICKERS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR",
    "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK",
    "BAJFINANCE", "MARUTI", "ASIANPAINT", "SUNPHARMA", "TATASTEEL",
    "WIPRO", "HCLTECH", "ONGC", "NTPC", "POWERGRID", "COALINDIA",
    "HINDALCO", "TATAMOTORS", "ADANIPORTS", "TECHM", "DRREDDY",
    "CIPLA", "BPCL", "ULTRACEMCO", "AMBUJACEM", "DABUR", "BRITANNIA",
    "HEROMOTOCO", "EICHERMOT", "TITAN", "MARICO", "VEDL", "JSPL",
    "GRASIM", "SHREECEM", "BAJAJAUTO", "M&M", "ADANIENT",
    "DIVISLAB", "INDUSINDBK", "TATAPOWER", "TATAELXSI", "PIDILITIND",
    "GODREJCP", "HAVELLS", "BAJAJFINSV", "LUPIN", "BAJAJHLDNG",
    "CANBK", "BANKBARODA", "UNIONBANK", "PNB", "FEDERALBNK",
    "IDFCFIRSTB", "HDFCLIFE", "SBILIFE", "ICICIPRULI", "SAIL",
    "NMDC", "NALCO", "NHPC", "POWERINDIA", "IOCL",
    "HPCL", "MUTHOOTFIN", "BANDHANBNK", "TORNTPHARM",
    "ALKEM", "LALPATHLAB", "BIOCON", "ZYDUSLIFE", "ABBOTINDIA",
    "APOLLOHOSP", "MAXHEALTH", "FORTIS", "DEVYANI", "OBEROIRLTY",
    "INDIANHOTL", "TVSMOTOR", "VOLTAS", "ASTRAL", "AARTIIND",
    "TORNTPOWER", "M&MFIN", "CHOLAFIN", "ICICIGI",
]

YEARS = list(range(2005, 2025))  # 20 years

COMPANY_NAMES = {
    "RELIANCE": "Reliance Industries Ltd", "TCS": "Tata Consultancy Services Ltd",
    "HDFCBANK": "HDFC Bank Ltd", "INFY": "Infosys Ltd",
    "ICICIBANK": "ICICI Bank Ltd", "HINDUNILVR": "Hindustan Unilever Ltd",
    "SBIN": "State Bank of India", "BHARTIARTL": "Bharti Airtel Ltd",
    "ITC": "ITC Ltd", "KOTAKBANK": "Kotak Mahindra Bank Ltd",
    "LT": "Larsen & Toubro Ltd", "AXISBANK": "Axis Bank Ltd",
    "BAJFINANCE": "Bajaj Finance Ltd", "MARUTI": "Maruti Suzuki India Ltd",
    "ASIANPAINT": "Asian Paints Ltd", "SUNPHARMA": "Sun Pharmaceutical Industries Ltd",
    "TATASTEEL": "Tata Steel Ltd", "WIPRO": "Wipro Ltd",
    "HCLTECH": "HCL Technologies Ltd", "ONGC": "Oil & Natural Gas Corporation Ltd",
    "NTPC": "NTPC Ltd", "POWERGRID": "Power Grid Corporation of India Ltd",
    "COALINDIA": "Coal India Ltd", "HINDALCO": "Hindalco Industries Ltd",
    "TATAMOTORS": "Tata Motors Ltd", "ADANIPORTS": "Adani Ports & SEZ Ltd",
    "TECHM": "Tech Mahindra Ltd", "DRREDDY": "Dr. Reddys Laboratories Ltd",
    "CIPLA": "Cipla Ltd", "BPCL": "Bharat Petroleum Corporation Ltd",
    "ULTRACEMCO": "UltraTech Cement Ltd", "AMBUJACEM": "Ambuja Cements Ltd",
    "DABUR": "Dabur India Ltd", "BRITANNIA": "Britannia Industries Ltd",
    "HEROMOTOCO": "Hero MotoCorp Ltd", "EICHERMOT": "Eicher Motors Ltd",
    "TITAN": "Titan Company Ltd", "MARICO": "Marico Ltd",
    "VEDL": "Vedanta Ltd", "JSPL": "Jindal Steel & Power Ltd",
    "GRASIM": "Grasim Industries Ltd", "SHREECEM": "Shree Cement Ltd",
    "BAJAJAUTO": "Bajaj Auto Ltd", "M&M": "Mahindra & Mahindra Ltd",
    "ADANIENT": "Adani Enterprises Ltd", "DIVISLAB": "Divis Laboratories Ltd",
    "INDUSINDBK": "IndusInd Bank Ltd", "TATAPOWER": "Tata Power Company Ltd",
    "TATAELXSI": "Tata Elxsi Ltd", "PIDILITIND": "Pidilite Industries Ltd",
    "GODREJCP": "Godrej Consumer Products Ltd", "HAVELLS": "Havells India Ltd",
    "BAJAJFINSV": "Bajaj Finserv Ltd", "LUPIN": "Lupin Ltd",
    "BAJAJHLDNG": "Bajaj Holdings & Investment Ltd", "CANBK": "Canara Bank Ltd",
    "BANKBARODA": "Bank of Baroda Ltd", "UNIONBANK": "Union Bank of India Ltd",
    "PNB": "Punjab National Bank Ltd", "FEDERALBNK": "Federal Bank Ltd",
    "IDFCFIRSTB": "IDFC First Bank Ltd", "HDFCLIFE": "HDFC Life Insurance Company Ltd",
    "SBILIFE": "SBI Life Insurance Company Ltd", "ICICIPRULI": "ICICI Prudential Life Insurance Ltd",
    "SAIL": "Steel Authority of India Ltd", "NMDC": "NMDC Ltd",
    "NALCO": "National Aluminium Company Ltd", "NHPC": "NHPC Ltd",
    "POWERINDIA": "Power Finance Corporation Ltd", "IOCL": "Indian Oil Corporation Ltd",
    "HPCL": "Hindustan Petroleum Corporation Ltd", "MUTHOOTFIN": "Muthoot Finance Ltd",
    "BANDHANBNK": "Bandhan Bank Ltd", "TORNTPHARM": "Torrent Pharmaceuticals Ltd",
    "ALKEM": "Alkem Laboratories Ltd", "LALPATHLAB": "Dr. Lal PathLabs Ltd",
    "BIOCON": "Biocon Ltd", "ZYDUSLIFE": "Zydus Lifesciences Ltd",
    "ABBOTINDIA": "Abbott India Ltd", "APOLLOHOSP": "Apollo Hospitals Enterprise Ltd",
    "MAXHEALTH": "Max Healthcare Institute Ltd", "FORTIS": "Fortis Healthcare Ltd",
    "DEVYANI": "Devyani International Ltd", "OBEROIRLTY": "Oberoi Realty Ltd",
    "INDIANHOTL": "Indian Hotels Company Ltd", "TVSMOTOR": "TVS Motor Company Ltd",
    "VOLTAS": "Voltas Ltd", "ASTRAL": "Astral Ltd",
    "AARTIIND": "Aarti Industries Ltd", "TORNTPOWER": "Torrent Power Ltd",
    "M&MFIN": "Mahindra & Mahindra Financial Services Ltd",
    "CHOLAFIN": "Cholamandalam Investment and Finance Company Ltd",
    "ICICIGI": "ICICI Lombard General Insurance Company Ltd",
}


def _assign_sectors():
    sector_map = {}
    for i, t in enumerate(TICKERS):
        sector_map[t] = SECTORS[i % len(SECTORS)]
    return sector_map


def _gen_sectors_df():
    rows = []
    for i, s in enumerate(SECTORS, 1):
        rows.append({"sector_id": i, "sector_name": s})
    return pd.DataFrame(rows)


def _gen_companies_df(tickers, sector_map):
    rows = []
    for i, t in enumerate(tickers, 1):
        mcap = round(random.uniform(5000, 800000), 2)
        rows.append({
            "ticker": t,
            "company_name": COMPANY_NAMES.get(t, f"{t} Ltd"),
            "sector_id": SECTORS.index(sector_map[t]) + 1,
            "bse_code": f"5{i:05d}",
            "nse_code": t,
            "isin": f"INE{i:06d}010",
            "listed_date": f"{random.choice(['15','20','28'])}-{random.choice(['01','03','06','09'])}-{random.randint(1995,2020)}",
            "market_cap_cr": mcap,
            "website": f"https://www.{t.lower()}.com",
            "description": f"{COMPANY_NAMES.get(t, t)} is a leading Indian company in the {sector_map[t]} sector.",
        })
    return pd.DataFrame(rows)


def _gen_pl_df(tickers, years):
    rows = []
    for t in tickers:
        n_years = min(len(years), random.randint(12, 16))
        t_years = sorted(random.sample(years, n_years))
        base_sales = random.uniform(500, 80000)
        for yr in t_years:
            base_sales *= (1 + random.uniform(-0.05, 0.20))
            sales = max(round(base_sales + random.uniform(-500, 1000), 2), 100)
            other_income = round(sales * random.uniform(0.01, 0.05), 2)
            total_income = round(sales + other_income, 2)
            opm_pct = random.uniform(0.10, 0.40)
            total_expense = round(total_income * (1 - opm_pct), 2)
            op_profit = round(total_income - total_expense, 2)
            interest = round(sales * random.uniform(0.01, 0.08), 2)
            dep_amort = round(sales * random.uniform(0.03, 0.08), 2)
            pbt = round(op_profit - interest - dep_amort, 2)
            tax_rate = random.uniform(0.20, 0.35)
            tax = round(max(pbt * tax_rate, 0), 2)
            net_profit = round(pbt - tax, 2)
            shares_cr = random.uniform(10, 500)
            eps = round(net_profit / shares_cr, 2)
            div_pct = random.uniform(0, 0.60)
            dividend_payout = round(net_profit * div_pct, 2)
            rows.append({
                "ticker": t, "year": yr, "sales": sales,
                "other_income": other_income, "total_income": total_income,
                "total_expense": total_expense, "opm": round(opm_pct * 100, 2),
                "op_profit": op_profit, "interest": interest,
                "dep_amort": dep_amort, "pbt": pbt, "tax": tax,
                "net_profit": net_profit, "eps": eps,
                "dividend_payout": dividend_payout, "dividend_pct": round(div_pct * 100, 2),
            })
    return pd.DataFrame(rows)


def _gen_bs_df(tickers, years):
    rows = []
    for t in tickers:
        n_years = min(len(years), random.randint(12, 16))
        t_years = sorted(random.sample(years, n_years))
        for yr in t_years:
            total_assets = round(random.uniform(2000, 500000), 2)
            current_ratio = random.uniform(0.8, 2.5)
            current_assets = round(total_assets * current_ratio / (1 + current_ratio), 2)
            current_liab = round(current_assets / current_ratio, 2)
            non_current_liab = round(total_assets * random.uniform(0.10, 0.35), 2)
            total_liab = round(current_liab + non_current_liab, 2)
            equity = round(total_assets - total_liab, 2)
            total_debt = round(total_liab * random.uniform(0.30, 0.70), 2)
            cash_equiv = round(current_assets * random.uniform(0.10, 0.40), 2)
            reserves = round(equity * random.uniform(0.40, 0.80), 2)
            borrowings = round(total_debt * random.uniform(0.60, 1.0), 2)
            rows.append({
                "ticker": t, "year": yr, "total_assets": total_assets,
                "current_assets": current_assets, "current_liab": current_liab,
                "non_current_liab": non_current_liab, "total_liab": total_liab,
                "equity": equity, "total_debt": total_debt,
                "cash_equiv": cash_equiv, "reserves": reserves,
                "borrowings": borrowings,
            })
    return pd.DataFrame(rows)


def _gen_cf_df(tickers, years):
    rows = []
    for t in tickers:
        n_years = min(len(years), random.randint(11, 15))
        t_years = sorted(random.sample(years, n_years))
        for yr in t_years:
            cfo = round(random.uniform(-2000, 15000), 2)
            cfi = round(random.uniform(-8000, 2000), 2)
            cff = round(random.uniform(-5000, 3000), 2)
            net_cash = round(cfo + cfi + cff, 2)
            capex = round(abs(random.uniform(500, 5000)), 2)
            div_paid = round(abs(random.uniform(0, 2000)), 2)
            rows.append({
                "ticker": t, "year": yr, "cfo": cfo, "cfi": cfi, "cff": cff,
                "net_cash": net_cash, "capex": capex, "div_paid": div_paid,
            })
    return pd.DataFrame(rows)


def _gen_stock_prices_df(tickers):
    rows = []
    dates = pd.date_range("2020-01-01", "2024-12-31", freq="B")
    rows_per_company = 5520 // len(tickers)
    for t in tickers:
        sample_dates = sorted(random.sample(list(dates), min(rows_per_company, len(dates))))
        base_price = random.uniform(100, 3000)
        for dt in sample_dates:
            base_price *= (1 + random.uniform(-0.05, 0.05))
            base_price = max(base_price, 10)
            open_p = round(base_price * random.uniform(0.98, 1.02), 2)
            high = round(max(open_p, base_price) * random.uniform(1.0, 1.04), 2)
            low = round(min(open_p, base_price) * random.uniform(0.96, 1.0), 2)
            close = round(base_price, 2)
            volume = random.randint(10000, 5000000)
            vwap = round((high + low + close) / 3, 2)
            rows.append({
                "ticker": t, "date": dt.strftime("%Y-%m-%d"),
                "open": open_p, "high": high, "low": low,
                "close": close, "volume": volume, "vwap": vwap,
            })
    return pd.DataFrame(rows).head(5520)


def _gen_financial_ratios_df(tickers, years):
    rows = []
    for t in tickers:
        n_years = min(len(years), random.randint(12, 16))
        t_years = sorted(random.sample(years, n_years))
        for yr in t_years:
            rows.append({
                "ticker": t, "year": yr,
                "pe_ratio": round(random.uniform(5, 80), 2),
                "pb_ratio": round(random.uniform(0.5, 15), 2),
                "ps_ratio": round(random.uniform(0.5, 12), 2),
                "ev_ebitda": round(random.uniform(4, 40), 2),
                "div_yield": round(random.uniform(0, 5), 2),
                "beta": round(random.uniform(0.3, 1.8), 2),
                "sharpe": round(random.uniform(-0.5, 2.5), 2),
            })
    return pd.DataFrame(rows)


def _gen_analysis_df(tickers, years):
    rows = []
    for t in tickers:
        n_years = min(len(years), random.randint(12, 16))
        t_years = sorted(random.sample(years, n_years))
        for yr in t_years:
            cr = round(random.uniform(0.5, 3.0), 2)
            rows.append({
                "ticker": t, "year": yr,
                "roe": round(random.uniform(2, 30), 2),
                "roa": round(random.uniform(1, 15), 2),
                "roce": round(random.uniform(5, 25), 2),
                "debt_to_equity": round(random.uniform(0.1, 3.0), 2),
                "interest_cov": round(random.uniform(1, 10), 2),
                "current_ratio": cr,
                "quick_ratio": round(cr * random.uniform(0.5, 0.9), 2),
                "net_margin": round(random.uniform(2, 25), 2),
                "asset_turnover": round(random.uniform(0.3, 2.0), 2),
                "retention_ratio": round(random.uniform(0.2, 0.9), 2),
            })
    return pd.DataFrame(rows)


def _gen_documents_df(tickers):
    rows = []
    doc_types = ["annual_report", "quarterly", "credit_rating"]
    for t in tickers:
        for _ in range(random.randint(2, 6)):
            dt = random.choice(doc_types)
            yr = random.randint(2018, 2024)
            rows.append({
                "ticker": t, "doc_type": dt,
                "doc_url": f"https://www.bseindia.com/{t.lower()}/{dt}_{yr}.pdf",
                "doc_date": f"{random.randint(1,28):02d}-{random.choice(['03','06','09','12'])}-{yr}",
                "description": f"{dt.replace('_',' ').title()} for {t} - {yr}",
            })
    return pd.DataFrame(rows)


def _gen_prosandcons_df(tickers):
    pros = [
        "Strong market position with consistent revenue growth",
        "Robust return on equity and capital efficiency",
        "Well-diversified revenue streams across segments",
        "Experienced management team with proven track record",
        "Healthy cash flow generation and low debt levels",
        "Strong brand recognition and customer loyalty",
        "Growing market share in key business segments",
        "Strategic acquisitions enhancing competitive position",
        "Consistent dividend payout history",
        "Strong digital transformation initiatives",
    ]
    cons = [
        "High valuation multiples compared to peers",
        "Exposure to regulatory and compliance risks",
        "Significant foreign currency fluctuation impact",
        "Intense competition in core business segments",
        "Rising raw material costs pressuring margins",
        "Dependence on a few key clients or products",
        "High debt levels constraining growth",
        "Vulnerability to economic downturns",
        "Geopolitical risks affecting supply chains",
        "Slow adoption of new technologies",
    ]
    rows = []
    for t in tickers:
        for _ in range(random.randint(2, 5)):
            rows.append({"ticker": t, "point_type": "pro", "point_text": random.choice(pros),
                         "category": random.choice(["Growth", "Financial", "Market", "Management"])})
        for _ in range(random.randint(1, 4)):
            rows.append({"ticker": t, "point_type": "con", "point_text": random.choice(cons),
                         "category": random.choice(["Risk", "Valuation", "Competition", "Macro"])})
    return pd.DataFrame(rows)


def _gen_peer_groups_df(tickers, sector_map):
    sector_groups = {}
    for t in tickers:
        s = sector_map[t]
        sector_groups.setdefault(s, []).append(t)
    rows = []
    for group_name, members in sector_groups.items():
        for t in members:
            rows.append({"group_name": group_name, "ticker": t})
    return pd.DataFrame(rows)


def _gen_sectors_supplementary_df():
    rows = []
    for s in SECTORS:
        rows.append({
            "sector_name": s,
            "avg_pe": round(random.uniform(10, 50), 2),
            "market_weight_pct": round(random.uniform(1, 15), 2),
            "ytd_return_pct": round(random.uniform(-10, 30), 2),
            "num_companies": random.randint(3, 10),
        })
    return pd.DataFrame(rows)


def main():
    print("Generating sample data for Nifty 100 ETL pipeline...")
    sector_map = _assign_sectors()
    tickers = TICKERS[:92]

    files = [
        ("sectors.xlsx", _gen_sectors_df, ()),
        ("companies.xlsx", _gen_companies_df, (tickers, sector_map,)),
        ("profitandloss.xlsx", _gen_pl_df, (tickers, YEARS)),
        ("balancesheet.xlsx", _gen_bs_df, (tickers, YEARS)),
        ("cashflow.xlsx", _gen_cf_df, (tickers, YEARS)),
        ("stock_prices.xlsx", _gen_stock_prices_df, (tickers,)),
        ("financial_ratios.xlsx", _gen_financial_ratios_df, (tickers, YEARS)),
        ("analysis.xlsx", _gen_analysis_df, (tickers, YEARS)),
        ("documents.xlsx", _gen_documents_df, (tickers,)),
        ("prosandcons.xlsx", _gen_prosandcons_df, (tickers,)),
        ("peer_groups.xlsx", _gen_peer_groups_df, (tickers, sector_map)),
        ("sectors_supplementary.xlsx", _gen_sectors_supplementary_df, ()),
    ]

    for idx, (fname, gen_fn, args) in enumerate(files, 1):
        print(f"  [{idx:2d}/12] {fname}")
        df = gen_fn(*args)
        df.to_excel(os.path.join(RAW_DIR, fname), index=False)

    print(f"\nDone! 12 files written to {RAW_DIR}/")


if __name__ == "__main__":
    main()