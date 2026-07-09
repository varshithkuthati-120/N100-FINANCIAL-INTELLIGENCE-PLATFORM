"""
validator.py — Run all 16 Data Quality rules against nifty100.db.

Severity levels:
    CRITICAL  — must be fixed before proceeding (PK/FK failures)
    WARNING   — should be reviewed but not blocking (OPM, balance, sales)

Outputs:
    output/validation_failures.csv

Usage:
    python -m src.etl.validator
"""

import csv
import sqlite3
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run_dq01(conn) -> list:
    """DQ-01: PK uniqueness — companies.ticker must be unique."""
    rows = conn.execute("""
        SELECT ticker, COUNT(*) as cnt
        FROM companies GROUP BY ticker HAVING cnt > 1
    """).fetchall()
    return [{"rule": "DQ-01", "severity": "CRITICAL", "table": "companies",
             "column": "ticker", "value": r[0], "detail": f"duplicate count={r[1]}"} for r in rows]


def run_dq02(conn) -> list:
    """DQ-02: (company_id, year) PK uniqueness in financial tables."""
    failures = []
    for tbl in ["profitandloss", "balancesheet", "cashflow", "analysis", "financial_ratios"]:
        rows = conn.execute(f"""
            SELECT company_id, year, COUNT(*) as cnt
            FROM {tbl} GROUP BY company_id, year HAVING cnt > 1
        """).fetchall()
        for r in rows:
            ticker = conn.execute(
                "SELECT ticker FROM companies WHERE company_id = ?", (r[0],)
            ).fetchone()
            t = ticker[0] if ticker else r[0]
            failures.append({"rule": "DQ-02", "severity": "CRITICAL", "table": tbl,
                             "column": "company_id,year", "value": f"{t}/{r[1]}",
                             "detail": f"duplicate count={r[2]}"})
    return failures


def run_dq03(conn) -> list:
    """DQ-03: FK integrity — PRAGMA foreign_key_check."""
    rows = conn.execute("PRAGMA foreign_key_check").fetchall()
    return [{"rule": "DQ-03", "severity": "CRITICAL", "table": str(r[0]),
             "column": str(r[1]), "value": str(r[2]),
             "detail": f"FK violation: parent={r[1]}, rowid={r[2]}"} for r in rows]


def run_dq04(conn) -> list:
    """DQ-04: Balance Sheet balance — |total_assets - (total_liab + equity)| / total_assets < 1%."""
    failures = []
    rows = conn.execute("""
        SELECT bs.id, c.ticker, bs.year, bs.total_assets, bs.total_liab, bs.equity,
               ABS(bs.total_assets - (bs.total_liab + bs.equity)) / NULLIF(bs.total_assets, 0) as pct
        FROM balancesheet bs JOIN companies c ON bs.company_id = c.company_id
        WHERE bs.total_assets IS NOT NULL AND bs.total_assets != 0
          AND ABS(bs.total_assets - (bs.total_liab + bs.equity)) / bs.total_assets >= 0.01
    """).fetchall()
    for r in rows:
        failures.append({"rule": "DQ-04", "severity": "WARNING", "table": "balancesheet",
                         "column": "balance_check", "value": f"{r[1]}/{r[2]}",
                         "detail": f"imbalance={r[6]*100:.2f}%, assets={r[3]}, liab+eq={r[4]+r[5]}"})
    return failures


def run_dq05(conn) -> list:
    """DQ-05: OPM cross-check — opm should roughly equal (op_profit / total_income * 100) ± 5pp."""
    failures = []
    rows = conn.execute("""
        SELECT pl.id, c.ticker, pl.year, pl.opm,
               CASE WHEN pl.total_income != 0
                    THEN ABS(pl.opm - (pl.op_profit / pl.total_income * 100))
                    ELSE 999 END as diff
        FROM profitandloss pl JOIN companies c ON pl.company_id = c.company_id
        WHERE pl.total_income IS NOT NULL AND pl.total_income != 0
          AND ABS(pl.opm - (pl.op_profit / pl.total_income * 100)) > 5
    """).fetchall()
    for r in rows:
        failures.append({"rule": "DQ-05", "severity": "WARNING", "table": "profitandloss",
                         "column": "opm", "value": f"{r[1]}/{r[2]}",
                         "detail": f"opm={r[3]}, computed={r[3]-r[4]+r[4]:.2f}, diff={r[4]:.2f}pp"})
    return failures


def run_dq06(conn) -> list:
    """DQ-06: Positive sales — sales should be > 0 for valid P&L rows."""
    rows = conn.execute("""
        SELECT pl.id, c.ticker, pl.year, pl.sales
        FROM profitandloss pl JOIN companies c ON pl.company_id = c.company_id
        WHERE pl.sales IS NOT NULL AND pl.sales <= 0
    """).fetchall()
    return [{"rule": "DQ-06", "severity": "WARNING", "table": "profitandloss",
             "column": "sales", "value": f"{r[1]}/{r[2]}", "detail": f"sales={r[3]}"}
            for r in rows]


def run_dq07(conn) -> list:
    """DQ-07: Net cash reasonability — net_cash should be within -50000 to +50000 Cr."""
    rows = conn.execute("""
        SELECT cf.id, c.ticker, cf.year, cf.net_cash
        FROM cashflow cf JOIN companies c ON cf.company_id = c.company_id
        WHERE cf.net_cash < -50000 OR cf.net_cash > 50000
    """).fetchall()
    return [{"rule": "DQ-07", "severity": "WARNING", "table": "cashflow",
             "column": "net_cash", "value": f"{r[1]}/{r[2]}", "detail": f"net_cash={r[3]}"}
            for r in rows]


def run_dq08(conn) -> list:
    """DQ-08: Tax rate — tax / pbt should be between 0% and 45% (Indian corporate tax range)."""
    rows = conn.execute("""
        SELECT pl.id, c.ticker, pl.year, pl.tax, pl.pbt,
               CASE WHEN pl.pbt > 0 THEN (pl.tax / pl.pbt * 100) ELSE NULL END as rate
        FROM profitandloss pl JOIN companies c ON pl.company_id = c.company_id
        WHERE pl.pbt IS NOT NULL AND pl.pbt > 0
          AND (pl.tax / pl.pbt * 100) > 45
    """).fetchall()
    return [{"rule": "DQ-08", "severity": "WARNING", "table": "profitandloss",
             "column": "tax_rate", "value": f"{r[1]}/{r[2]}",
             "detail": f"tax={r[3]}, pbt={r[4]}, rate={r[5]:.1f}%"} for r in rows]


def run_dq09(conn) -> list:
    """DQ-09: Dividend payout cap — dividend_payout should not exceed net_profit (when net_profit > 0)."""
    rows = conn.execute("""
        SELECT pl.id, c.ticker, pl.year, pl.dividend_payout, pl.net_profit
        FROM profitandloss pl JOIN companies c ON pl.company_id = c.company_id
        WHERE pl.net_profit IS NOT NULL AND pl.net_profit > 0
          AND pl.dividend_payout > pl.net_profit
    """).fetchall()
    return [{"rule": "DQ-09", "severity": "WARNING", "table": "profitandloss",
             "column": "dividend_payout", "value": f"{r[1]}/{r[2]}",
             "detail": f"dividend={r[3]}, net_profit={r[4]}"} for r in rows]


def run_dq10(conn) -> list:
    """DQ-10: URL validity — company website should start with http:// or https://."""
    rows = conn.execute("""
        SELECT company_id, ticker, website
        FROM companies
        WHERE website IS NOT NULL AND website != ''
          AND website NOT LIKE 'http://%'
          AND website NOT LIKE 'https://%'
    """).fetchall()
    return [{"rule": "DQ-10", "severity": "WARNING", "table": "companies",
             "column": "website", "value": r[1], "detail": f"invalid URL: {r[2]}"}
            for r in rows]


def run_dq11(conn) -> list:
    """DQ-11: EPS sign consistency — EPS and net_profit should have the same sign."""
    rows = conn.execute("""
        SELECT pl.id, c.ticker, pl.year, pl.eps, pl.net_profit
        FROM profitandloss pl JOIN companies c ON pl.company_id = c.company_id
        WHERE (pl.eps > 0 AND pl.net_profit < 0)
           OR (pl.eps < 0 AND pl.net_profit > 0)
    """).fetchall()
    return [{"rule": "DQ-11", "severity": "WARNING", "table": "profitandloss",
             "column": "eps", "value": f"{r[1]}/{r[2]}",
             "detail": f"eps={r[3]}, net_profit={r[4]}"} for r in rows]


def run_dq12(conn) -> list:
    """DQ-12: BSE balance check — similar to DQ-04 but for a different tolerance threshold (0.5%)."""
    failures = []
    rows = conn.execute("""
        SELECT bs.id, c.ticker, bs.year, bs.total_assets, bs.total_liab, bs.equity,
               ABS(bs.total_assets - (bs.total_liab + bs.equity)) / NULLIF(bs.total_assets, 0) as pct
        FROM balancesheet bs JOIN companies c ON bs.company_id = c.company_id
        WHERE bs.total_assets IS NOT NULL AND bs.total_assets != 0
          AND ABS(bs.total_assets - (bs.total_liab + bs.equity)) / bs.total_assets >= 0.005
    """).fetchall()
    for r in rows:
        failures.append({"rule": "DQ-12", "severity": "WARNING", "table": "balancesheet",
                         "column": "bse_balance", "value": f"{r[1]}/{r[2]}",
                         "detail": f"imbalance={r[6]*100:.3f}% >= 0.5%"})
    return failures


def run_dq13(conn) -> list:
    """DQ-13: Year coverage — companies should have at least 5 years of financial data."""
    failures = []
    for tbl in ["profitandloss", "balancesheet", "cashflow"]:
        rows = conn.execute(f"""
            SELECT c.ticker, COUNT(DISTINCT pl.year) as yr_cnt
            FROM {tbl} pl JOIN companies c ON pl.company_id = c.company_id
            GROUP BY pl.company_id HAVING yr_cnt < 5
        """).fetchall()
        for r in rows:
            failures.append({"rule": "DQ-13", "severity": "WARNING", "table": tbl,
                             "column": "year_coverage", "value": r[0],
                             "detail": f"only {r[1]} years in {tbl}"})
    return failures


def run_dq14(conn) -> list:
    """DQ-14: Stock price OHLC sanity — high >= low, high >= open, high >= close."""
    rows = conn.execute("""
        SELECT id, company_id, date, open, high, low, close
        FROM stock_prices
        WHERE high < low OR high < open OR high < close OR low > open OR low > close
    """).fetchall()
    failures = []
    for r in rows:
        ticker = conn.execute(
            "SELECT ticker FROM companies WHERE company_id = ?", (r[1],)
        ).fetchone()
        t = ticker[0] if ticker else str(r[1])
        failures.append({"rule": "DQ-14", "severity": "CRITICAL", "table": "stock_prices",
                         "column": "ohlc", "value": f"{t}/{r[2]}",
                         "detail": f"O={r[3]},H={r[4]},L={r[5]},C={r[6]}"})
    return failures


def run_dq15(conn) -> list:
    """DQ-15: Financial ratios range check — PE, PB should be within reasonable bounds."""
    rows = conn.execute("""
        SELECT fr.id, c.ticker, fr.year, fr.pe_ratio, fr.pb_ratio
        FROM financial_ratios fr JOIN companies c ON fr.company_id = c.company_id
        WHERE fr.pe_ratio < -50 OR fr.pe_ratio > 200
           OR fr.pb_ratio < -10 OR fr.pb_ratio > 100
    """).fetchall()
    return [{"rule": "DQ-15", "severity": "WARNING", "table": "financial_ratios",
             "column": "pe_pb_range", "value": f"{r[1]}/{r[2]}",
             "detail": f"PE={r[3]}, PB={r[4]}"} for r in rows]


def run_dq16(conn) -> list:
    """DQ-16: Sector assignment — every company must have a valid sector_id in sectors table."""
    rows = conn.execute("""
        SELECT c.company_id, c.ticker, c.sector_id
        FROM companies c
        LEFT JOIN sectors s ON c.sector_id = s.sector_id
        WHERE s.sector_id IS NULL
    """).fetchall()
    return [{"rule": "DQ-16", "severity": "CRITICAL", "table": "companies",
             "column": "sector_id", "value": r[1],
             "detail": f"sector_id={r[2]} not found in sectors"} for r in rows]


# ── Registry & runner ──────────────────────────────────────

ALL_RULES = [
    ("DQ-01", "PK uniqueness (companies.ticker)", run_dq01),
    ("DQ-02", "Composite PK uniqueness (company_id, year)", run_dq02),
    ("DQ-03", "FK integrity (PRAGMA foreign_key_check)", run_dq03),
    ("DQ-04", "BS balance < 1% tolerance", run_dq04),
    ("DQ-05", "OPM cross-check ± 5pp", run_dq05),
    ("DQ-06", "Positive sales", run_dq06),
    ("DQ-07", "Net cash reasonability (-50000 to +50000)", run_dq07),
    ("DQ-08", "Tax rate ≤ 45%", run_dq08),
    ("DQ-09", "Dividend payout ≤ net_profit", run_dq09),
    ("DQ-10", "URL validity (http/https)", run_dq10),
    ("DQ-11", "EPS sign consistency", run_dq11),
    ("DQ-12", "BSE balance check < 0.5%", run_dq12),
    ("DQ-13", "Year coverage ≥ 5 years", run_dq13),
    ("DQ-14", "Stock price OHLC sanity", run_dq14),
    ("DQ-15", "Financial ratios range check", run_dq15),
    ("DQ-16", "Sector assignment validity", run_dq16),
]


def run_all(conn) -> list:
    """Run all 16 DQ rules. Returns flat list of failure dicts."""
    all_failures = []
    for rule_id, desc, fn in ALL_RULES:
        failures = fn(conn)
        severity_counts = {}
        for f in failures:
            severity_counts[f["severity"]] = severity_counts.get(f["severity"], 0) + 1
        status = "PASS" if not failures else ", ".join(f"{k}:{v}" for k, v in severity_counts.items())
        print(f"  {rule_id} {desc:50s} {status}")
        all_failures.extend(failures)
    return all_failures


def write_failures(failures: list, path: Path):
    fields = ["rule", "severity", "table", "column", "value", "detail"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(failures)


def main():
    if not DB_PATH.exists():
        print(f"[ERROR] Database not found: {DB_PATH}")
        print("  Run the loader first: python -m src.etl.loader")
        sys.exit(1)

    print("=" * 70)
    print("NIFTY 100 — Data Quality Validation (16 DQ Rules)")
    print("=" * 70)

    conn = _get_conn()
    failures = run_all(conn)

    critical = [f for f in failures if f["severity"] == "CRITICAL"]
    warning = [f for f in failures if f["severity"] == "WARNING"]

    print(f"\n{'='*70}")
    print(f"RESULTS: {len(failures)} total failures  |  {len(critical)} CRITICAL  |  {len(warning)} WARNING")
    print(f"{'='*70}")

    out_path = OUTPUT_DIR / "validation_failures.csv"
    write_failures(failures, out_path)
    print(f"\n[OUTPUT] {out_path}")

    conn.close()
    return len(critical) == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)