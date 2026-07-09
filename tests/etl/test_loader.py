"""
test_loader.py — Integration tests for the ETL loader.

Tests verify:
    - Schema creates all 10 tables
    - Companies table has exactly 92 rows
    - FK check returns 0 violations
    - load_audit.csv is generated
"""

import csv
import os
import sqlite3
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "nifty100.db"
AUDIT_PATH = PROJECT_ROOT / "output" / "load_audit.csv"
SCHEMA_PATH = PROJECT_ROOT / "db" / "schema.sql"


@pytest.fixture(scope="module")
def conn():
    """Shared DB connection for all loader tests."""
    if not DB_PATH.exists():
        pytest.skip("nifty100.db not found — run loader first")
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


class TestLoaderSchema:
    """Verify schema and table structure."""

    def test_01_all_tables_exist(self, conn):
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()}
        expected = {
            "sectors", "companies", "profitandloss", "balancesheet",
            "cashflow", "stock_prices", "financial_ratios",
            "analysis", "documents", "prosandcons", "peer_groups",
        }
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"

    def test_02_companies_row_count(self, conn):
        cnt = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        assert cnt == 92, f"Expected 92 companies, got {cnt}"

    def test_03_fk_check_zero(self, conn):
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        assert len(violations) == 0, f"FK violations: {violations[:5]}"

    def test_04_profitandloss_has_data(self, conn):
        cnt = conn.execute("SELECT COUNT(*) FROM profitandloss").fetchone()[0]
        assert cnt >= 1000, f"P&L too few rows: {cnt}"

    def test_05_balancesheet_has_data(self, conn):
        cnt = conn.execute("SELECT COUNT(*) FROM balancesheet").fetchone()[0]
        assert cnt >= 1000, f"BS too few rows: {cnt}"

    def test_06_cashflow_has_data(self, conn):
        cnt = conn.execute("SELECT COUNT(*) FROM cashflow").fetchone()[0]
        assert cnt >= 1000, f"CF too few rows: {cnt}"

    def test_07_stock_prices_count(self, conn):
        cnt = conn.execute("SELECT COUNT(*) FROM stock_prices").fetchone()[0]
        assert cnt == 5520, f"Expected 5520 stock_prices, got {cnt}"


class TestLoaderAudit:
    """Verify load_audit.csv output."""

    def test_08_audit_file_exists(self):
        assert AUDIT_PATH.exists(), f"Audit file not found: {AUDIT_PATH}"

    def test_09_audit_has_all_tables(self):
        with open(AUDIT_PATH) as f:
            reader = csv.DictReader(f)
            tables = {row["table"] for row in reader}
        expected = {
            "sectors", "companies", "profitandloss", "balancesheet",
            "cashflow", "stock_prices", "financial_ratios",
            "analysis", "documents", "prosandcons", "peer_groups",
        }
        assert expected.issubset(tables)

    def test_10_audit_no_critical_rejections(self):
        with open(AUDIT_PATH) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["status"] not in ("OK", "FILE_NOT_FOUND", "SUPPLEMENTARY_ONLY"):
                    assert "CRITICAL" not in row["status"].upper()