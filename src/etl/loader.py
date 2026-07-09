"""
loader.py — Load all 12 Excel source files into nifty100.db.

Execution order (respects FK dependencies):
    1. sectors          (no FK)
    2. companies         (FK → sectors)
    3. profitandloss     (FK → companies)
    4. balancesheet      (FK → companies)
    5. cashflow          (FK → companies)
    6. stock_prices      (FK → companies)
    7. financial_ratios  (FK → companies)
    8. analysis          (FK → companies)
    9. documents         (FK → companies)
   10. prosandcons       (FK → companies)
   11. peer_groups       (FK → companies)

Outputs:
    nifty100.db              — SQLite database
    output/load_audit.csv    — per-table row counts & rejections

Usage:
    python -m src.etl.loader
"""

import csv
import os
import sqlite3
import sys
import time
from pathlib import Path

import pandas as pd

# Allow running as `python -m src.etl.loader`
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.normaliser import normalize_year, normalize_ticker

# ── Paths ──────────────────────────────────────────────────
DB_PATH = PROJECT_ROOT / "nifty100.db"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Helpers ────────────────────────────────────────────────
def _ticker_to_id(cursor, ticker: str) -> int:
    """Resolve canonical ticker → company_id (must exist in companies table)."""
    row = cursor.execute(
        "SELECT company_id FROM companies WHERE ticker = ?", (ticker,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Ticker '{ticker}' not found in companies table")
    return row[0]


def _sector_name_to_id(cursor, sector_name) -> int:
    row = cursor.execute(
        "SELECT sector_id FROM sectors WHERE sector_name = ?", (sector_name,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Sector '{sector_name}' not found")
    return row[0]


# ── Load functions (one per table) ────────────────────────

def load_sectors(conn, df) -> tuple:
    """Load sectors table. Returns (inserted, rejected)."""
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            cur.execute(
                "INSERT OR IGNORE INTO sectors (sector_name) VALUES (?)",
                (str(row.get("sector_name", "")).strip(),),
            )
            inserted += cur.rowcount
        except Exception as e:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_companies(conn, df) -> tuple:
    """Load companies table. Returns (inserted, rejected)."""
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            sector_id = int(row.get("sector_id", 1))
            cur.execute(
                """INSERT OR IGNORE INTO companies
                   (ticker, company_name, sector_id, bse_code, nse_code, isin,
                    listed_date, market_cap_cr, website, description)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (
                    ticker,
                    str(row.get("company_name", "")),
                    sector_id,
                    str(row.get("bse_code", "")),
                    str(row.get("nse_code", ticker)),
                    str(row.get("isin", "")),
                    str(row.get("listed_date", "")),
                    float(row.get("market_cap_cr", 0)),
                    str(row.get("website", "")),
                    str(row.get("description", "")),
                ),
            )
            inserted += cur.rowcount
        except Exception as e:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_profitandloss(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            year = normalize_year(row.get("year"))
            cur.execute(
                """INSERT OR IGNORE INTO profitandloss
                   (company_id, year, sales, other_income, total_income,
                    total_expense, opm, op_profit, interest, dep_amort,
                    pbt, tax, net_profit, eps, dividend_payout, dividend_pct)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid, year,
                    float(row.get("sales", 0) or 0),
                    float(row.get("other_income", 0) or 0),
                    float(row.get("total_income", 0) or 0),
                    float(row.get("total_expense", 0) or 0),
                    float(row.get("opm", 0) or 0),
                    float(row.get("op_profit", 0) or 0),
                    float(row.get("interest", 0) or 0),
                    float(row.get("dep_amort", 0) or 0),
                    float(row.get("pbt", 0) or 0),
                    float(row.get("tax", 0) or 0),
                    float(row.get("net_profit", 0) or 0),
                    float(row.get("eps", 0) or 0),
                    float(row.get("dividend_payout", 0) or 0),
                    float(row.get("dividend_pct", 0) or 0),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_balancesheet(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            year = normalize_year(row.get("year"))
            cur.execute(
                """INSERT OR IGNORE INTO balancesheet
                   (company_id, year, total_assets, current_assets, current_liab,
                    non_current_liab, total_liab, equity, total_debt,
                    cash_equiv, reserves, borrowings)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid, year,
                    float(row.get("total_assets", 0) or 0),
                    float(row.get("current_assets", 0) or 0),
                    float(row.get("current_liab", 0) or 0),
                    float(row.get("non_current_liab", 0) or 0),
                    float(row.get("total_liab", 0) or 0),
                    float(row.get("equity", 0) or 0),
                    float(row.get("total_debt", 0) or 0),
                    float(row.get("cash_equiv", 0) or 0),
                    float(row.get("reserves", 0) or 0),
                    float(row.get("borrowings", 0) or 0),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_cashflow(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            year = normalize_year(row.get("year"))
            cur.execute(
                """INSERT OR IGNORE INTO cashflow
                   (company_id, year, cfo, cfi, cff, net_cash, capex, div_paid)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    cid, year,
                    float(row.get("cfo", 0) or 0),
                    float(row.get("cfi", 0) or 0),
                    float(row.get("cff", 0) or 0),
                    float(row.get("net_cash", 0) or 0),
                    float(row.get("capex", 0) or 0),
                    float(row.get("div_paid", 0) or 0),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_stock_prices(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            date_str = str(row.get("date", "")).strip()
            if not date_str or len(date_str) < 10:
                rejected += 1
                continue
            cur.execute(
                """INSERT OR IGNORE INTO stock_prices
                   (company_id, date, open, high, low, close, volume, vwap)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (
                    cid, date_str,
                    float(row.get("open", 0) or 0),
                    float(row.get("high", 0) or 0),
                    float(row.get("low", 0) or 0),
                    float(row.get("close", 0) or 0),
                    int(row.get("volume", 0) or 0),
                    float(row.get("vwap", 0) or 0),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_financial_ratios(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            year = normalize_year(row.get("year"))
            cur.execute(
                """INSERT OR IGNORE INTO financial_ratios
                   (company_id, year, pe_ratio, pb_ratio, ps_ratio, ev_ebitda,
                    div_yield, beta, sharpe)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (
                    cid, year,
                    float(row.get("pe_ratio", 0) or 0),
                    float(row.get("pb_ratio", 0) or 0),
                    float(row.get("ps_ratio", 0) or 0),
                    float(row.get("ev_ebitda", 0) or 0),
                    float(row.get("div_yield", 0) or 0),
                    float(row.get("beta", 0) or 0),
                    float(row.get("sharpe", 0) or 0),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_analysis(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            year = normalize_year(row.get("year"))
            cur.execute(
                """INSERT OR IGNORE INTO analysis
                   (company_id, year, roe, roa, roce, debt_to_equity,
                    interest_cov, current_ratio, quick_ratio, net_margin,
                    asset_turnover, retention_ratio)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid, year,
                    float(row.get("roe", 0) or 0),
                    float(row.get("roa", 0) or 0),
                    float(row.get("roce", 0) or 0),
                    float(row.get("debt_to_equity", 0) or 0),
                    float(row.get("interest_cov", 0) or 0),
                    float(row.get("current_ratio", 0) or 0),
                    float(row.get("quick_ratio", 0) or 0),
                    float(row.get("net_margin", 0) or 0),
                    float(row.get("asset_turnover", 0) or 0),
                    float(row.get("retention_ratio", 0) or 0),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_documents(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            cur.execute(
                """INSERT OR IGNORE INTO documents
                   (company_id, doc_type, doc_url, doc_date, description)
                   VALUES (?,?,?,?,?)""",
                (
                    cid,
                    str(row.get("doc_type", "")).strip(),
                    str(row.get("doc_url", "")),
                    str(row.get("doc_date", "")),
                    str(row.get("description", "")),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_prosandcons(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            pt = str(row.get("point_type", "")).strip().lower()
            if pt not in ("pro", "con"):
                rejected += 1
                continue
            cur.execute(
                """INSERT OR IGNORE INTO prosandcons
                   (company_id, point_type, point_text, category)
                   VALUES (?,?,?,?)""",
                (
                    cid, pt,
                    str(row.get("point_text", "")),
                    str(row.get("category", "")),
                ),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


def load_peer_groups(conn, df) -> tuple:
    inserted, rejected = 0, 0
    cur = conn.cursor()
    for _, row in df.iterrows():
        try:
            ticker = normalize_ticker(row.get("ticker"))
            cid = _ticker_to_id(cur, ticker)
            group = str(row.get("group_name", "")).strip()
            if not group:
                rejected += 1
                continue
            cur.execute(
                "INSERT OR IGNORE INTO peer_groups (group_name, company_id) VALUES (?,?)",
                (group, cid),
            )
            inserted += cur.rowcount
        except Exception:
            rejected += 1
    conn.commit()
    return inserted, rejected


# ── Load order & dispatch ─────────────────────────────────

LOAD_ORDER = [
    ("sectors.xlsx",         "sectors",         load_sectors),
    ("companies.xlsx",       "companies",       load_companies),
    ("profitandloss.xlsx",   "profitandloss",   load_profitandloss),
    ("balancesheet.xlsx",    "balancesheet",    load_balancesheet),
    ("cashflow.xlsx",        "cashflow",        load_cashflow),
    ("stock_prices.xlsx",    "stock_prices",    load_stock_prices),
    ("financial_ratios.xlsx","financial_ratios",load_financial_ratios),
    ("analysis.xlsx",        "analysis",        load_analysis),
    ("documents.xlsx",       "documents",       load_documents),
    ("prosandcons.xlsx",     "prosandcons",     load_prosandcons),
    ("peer_groups.xlsx",     "peer_groups",     load_peer_groups),
]

# Supplementary files not loaded into DB but tracked
SUPPLEMENTARY_ONLY = ["sectors_supplementary.xlsx"]


def write_audit(records: list, path: Path):
    """Write load_audit.csv with columns: file, table, rows_inserted, rows_rejected, source_rows, status."""
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "file", "table", "source_rows", "rows_inserted", "rows_rejected", "status"
        ])
        writer.writeheader()
        for r in records:
            writer.writerow(r)


def main():
    t0 = time.time()

    # Remove stale DB
    if DB_PATH.exists():
        DB_PATH.unlink()

    # Create DB & apply schema
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    print(f"[OK] Schema applied from {SCHEMA_PATH}")

    audit = []

    for fname, table, load_fn in LOAD_ORDER:
        fpath = RAW_DIR / fname
        if not fpath.exists():
            print(f"[SKIP] {fname} not found in {RAW_DIR}")
            audit.append({
                "file": fname, "table": table,
                "source_rows": 0, "rows_inserted": 0, "rows_rejected": 0,
                "status": "FILE_NOT_FOUND",
            })
            continue

        print(f"[LOAD] {fname:30s} → {table}...", end=" ", flush=True)
        df = pd.read_excel(fpath)
        source_rows = len(df)
        inserted, rejected = load_fn(conn, df)
        status = "OK" if rejected == 0 else f"WARNING({rejected} rejected)"
        print(f"{source_rows} source → {inserted} inserted, {rejected} rejected  [{status}]")
        audit.append({
            "file": fname, "table": table,
            "source_rows": source_rows, "rows_inserted": inserted,
            "rows_rejected": rejected, "status": status,
        })

    # Track supplementary-only files
    for fname in SUPPLEMENTARY_ONLY:
        fpath = RAW_DIR / fname
        source_rows = 0
        if fpath.exists():
            source_rows = len(pd.read_excel(fpath))
        audit.append({
            "file": fname, "table": "(supplementary)",
            "source_rows": source_rows, "rows_inserted": 0, "rows_rejected": 0,
            "status": "SUPPLEMENTARY_ONLY",
        })

    # FK check
    fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    print(f"\n[FK CHECK] {len(fk_violations)} violation(s)")
    if fk_violations:
        for v in fk_violations:
            print(f"  {v}")

    # Row counts summary
    print("\n[ROW COUNTS]")
    table_order = [
        "sectors", "companies", "profitandloss", "balancesheet",
        "cashflow", "stock_prices", "financial_ratios",
        "analysis", "documents", "prosandcons", "peer_groups",
    ]
    for t in table_order:
        cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t:25s} {cnt:>6d} rows")

    # Write audit CSV
    audit_path = OUTPUT_DIR / "load_audit.csv"
    write_audit(audit, audit_path)
    print(f"\n[AUDIT] {audit_path}")

    conn.close()

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")


if __name__ == "__main__":
    main()