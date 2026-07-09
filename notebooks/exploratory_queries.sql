-- ============================================================
-- exploratory_queries.sql — 10 exploratory SQL queries
-- Run: sqlite3 nifty100.db < notebooks/exploratory_queries.sql
-- ============================================================

-- Q1: Total companies per sector
SELECT s.sector_name, COUNT(c.company_id) AS company_count
FROM sectors s
LEFT JOIN companies c ON s.sector_id = c.sector_id
GROUP BY s.sector_name
ORDER BY company_count DESC;

-- Q2: Top 10 companies by latest market cap
SELECT ticker, company_name, market_cap_cr, s.sector_name
FROM companies c JOIN sectors s ON c.sector_id = s.sector_id
ORDER BY market_cap_cr DESC
LIMIT 10;

-- Q3: Year-over-year revenue growth for top 5 companies (latest 3 years)
WITH ranked AS (
    SELECT c.ticker, pl.year, pl.sales,
           LAG(pl.sales) OVER (PARTITION BY c.company_id ORDER BY pl.year) AS prev_sales
    FROM profitandloss pl JOIN companies c ON pl.company_id = c.company_id
)
SELECT ticker, year, sales,
       ROUND((sales - prev_sales) / prev_sales * 100, 2) AS yoy_growth_pct
FROM ranked
WHERE prev_sales IS NOT NULL AND prev_sales > 0
ORDER BY ticker, year DESC;

-- Q4: Companies with highest average OPM (last 5 years)
SELECT c.ticker, c.company_name, ROUND(AVG(pl.opm), 2) AS avg_opm
FROM profitandloss pl JOIN companies c ON pl.company_id = c.company_id
WHERE pl.year >= 2020
GROUP BY c.company_id
ORDER BY avg_opm DESC
LIMIT 10;

-- Q5: Companies with debt-to-equity > 2 (from analysis table)
SELECT DISTINCT c.ticker, c.company_name, a.debt_to_equity, a.year
FROM analysis a JOIN companies c ON a.company_id = c.company_id
WHERE a.debt_to_equity > 2.0
ORDER BY a.debt_to_equity DESC;

-- Q6: Average PE ratio by sector
SELECT s.sector_name, ROUND(AVG(fr.pe_ratio), 2) AS avg_pe,
       COUNT(DISTINCT fr.company_id) AS num_companies
FROM financial_ratios fr
JOIN companies c ON fr.company_id = c.company_id
JOIN sectors s ON c.sector_id = s.sector_id
WHERE fr.year = 2024
GROUP BY s.sector_name
ORDER BY avg_pe DESC;

-- Q7: Companies with < 5 years of P&L data (DQ-13 manual review)
SELECT c.ticker, COUNT(pl.year) AS year_count
FROM companies c
LEFT JOIN profitandloss pl ON c.company_id = pl.company_id
GROUP BY c.company_id
HAVING year_count < 5
ORDER BY year_count ASC;

-- Q8: Top 10 most traded stocks by total volume
SELECT c.ticker, SUM(sp.volume) AS total_volume,
       COUNT(DISTINCT sp.date) AS trading_days
FROM stock_prices sp JOIN companies c ON sp.company_id = c.company_id
GROUP BY c.company_id
ORDER BY total_volume DESC
LIMIT 10;

-- Q9: Cash flow summary — companies with negative CFO in latest year
SELECT c.ticker, cf.year, cf.cfo, cf.cfi, cf.cff, cf.net_cash
FROM cashflow cf JOIN companies c ON cf.company_id = c.company_id
WHERE cf.year = (SELECT MAX(year) FROM cashflow) AND cf.cfo < 0
ORDER BY cf.cfo ASC;

-- Q10: Peer group comparison — ROE by sector (latest year)
SELECT s.sector_name, c.ticker, a.roe, a.roa, a.roce
FROM analysis a
JOIN companies c ON a.company_id = c.company_id
JOIN sectors s ON c.sector_id = s.sector_id
WHERE a.year = (SELECT MAX(year) FROM analysis)
ORDER BY s.sector_name, a.roe DESC;