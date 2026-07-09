-- ============================================================
-- Nifty 100 Analytics Database Schema
-- 10 tables · PK/FK · PRAGMA foreign_keys = ON
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- 1. companies (master table)
CREATE TABLE IF NOT EXISTS companies (
    company_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker        TEXT    NOT NULL UNIQUE,
    company_name  TEXT    NOT NULL,
    sector_id     INTEGER NOT NULL,
    bse_code      TEXT,
    nse_code      TEXT,
    isin          TEXT,
    listed_date   TEXT,
    market_cap_cr REAL,
    website       TEXT,
    description   TEXT,
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
);

-- 2. sectors (lookup)
CREATE TABLE IF NOT EXISTS sectors (
    sector_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    sector_name TEXT    NOT NULL UNIQUE
);

-- 3. profitandloss (P&L)
CREATE TABLE IF NOT EXISTS profitandloss (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id   INTEGER NOT NULL,
    year         INTEGER NOT NULL,
    sales        REAL,
    other_income REAL    DEFAULT 0,
    total_income REAL,
    total_expense REAL,
    opm          REAL,
    op_profit    REAL,
    interest     REAL    DEFAULT 0,
    dep_amort    REAL    DEFAULT 0,
    pbt          REAL,
    tax          REAL    DEFAULT 0,
    net_profit   REAL,
    eps          REAL,
    dividend_payout REAL DEFAULT 0,
    dividend_pct   REAL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(company_id, year)
);

-- 4. balancesheet (BS)
CREATE TABLE IF NOT EXISTS balancesheet (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    total_assets    REAL,
    current_assets  REAL,
    current_liab    REAL,
    non_current_liab REAL,
    total_liab      REAL,
    equity          REAL,
    total_debt      REAL,
    cash_equiv      REAL,
    reserves        REAL,
    borrowings      REAL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(company_id, year)
);

-- 5. cashflow (CF)
CREATE TABLE IF NOT EXISTS cashflow (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    cfo             REAL,   -- cash from operations
    cfi             REAL,   -- cash from investing
    cff             REAL,   -- cash from financing
    net_cash        REAL,
    capex           REAL    DEFAULT 0,
    div_paid        REAL    DEFAULT 0,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(company_id, year)
);

-- 6. analysis
CREATE TABLE IF NOT EXISTS analysis (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id    INTEGER NOT NULL,
    year          INTEGER NOT NULL,
    roe           REAL,
    roa           REAL,
    roce          REAL,
    debt_to_equity REAL,
    interest_cov  REAL,
    current_ratio REAL,
    quick_ratio   REAL,
    net_margin    REAL,
    asset_turnover REAL,
    retention_ratio REAL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(company_id, year)
);

-- 7. documents
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL,
    doc_type    TEXT    NOT NULL,  -- 'annual_report', 'quarterly', 'credit_rating'
    doc_url     TEXT,
    doc_date    TEXT,
    description TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- 8. prosandcons
CREATE TABLE IF NOT EXISTS prosandcons (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL,
    point_type  TEXT    NOT NULL CHECK(point_type IN ('pro', 'con')),
    point_text  TEXT    NOT NULL,
    category    TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- 9. stock_prices (daily)
CREATE TABLE IF NOT EXISTS stock_prices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL,
    date        TEXT    NOT NULL,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    volume      INTEGER,
    vwap        REAL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(company_id, date)
);

-- 10. financial_ratios
CREATE TABLE IF NOT EXISTS financial_ratios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id      INTEGER NOT NULL,
    year            INTEGER NOT NULL,
    pe_ratio        REAL,
    pb_ratio        REAL,
    ps_ratio        REAL,
    ev_ebitda       REAL,
    div_yield       REAL,
    beta            REAL,
    sharpe          REAL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(company_id, year)
);

-- 11. peer_groups
CREATE TABLE IF NOT EXISTS peer_groups (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name  TEXT    NOT NULL,
    company_id  INTEGER NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(group_name, company_id)
);

-- ============================================================
-- Indexes for common query patterns
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_pl_company ON profitandloss(company_id);
CREATE INDEX IF NOT EXISTS idx_pl_year ON profitandloss(year);
CREATE INDEX IF NOT EXISTS idx_bs_company ON balancesheet(company_id);
CREATE INDEX IF NOT EXISTS idx_bs_year ON balancesheet(year);
CREATE INDEX IF NOT EXISTS idx_cf_company ON cashflow(company_id);
CREATE INDEX IF NOT EXISTS idx_cf_year ON cashflow(year);
CREATE INDEX IF NOT EXISTS idx_sp_company ON stock_prices(company_id);
CREATE INDEX IF NOT EXISTS idx_sp_date ON stock_prices(date);
CREATE INDEX IF NOT EXISTS idx_fr_company ON financial_ratios(company_id);
CREATE INDEX IF NOT EXISTS idx_an_company ON analysis(company_id);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector_id);
CREATE INDEX IF NOT EXISTS idx_peer_group ON peer_groups(group_name);