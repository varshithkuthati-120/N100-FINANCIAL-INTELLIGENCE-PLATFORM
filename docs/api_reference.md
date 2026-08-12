# Nifty 100 API Reference

## Base URL
`/api/v1`

## Endpoints

### 1. Health
`GET /health`
Returns API health status, uptime, version, and database row counts.

### 2. Companies
`GET /companies`
Query Params: `sector`, `market_cap_category`, `search`
Returns a list of companies.

### 3. Company Profile
`GET /companies/{ticker}`
Returns detailed profile and latest KPIs for a specific company.

### 4. Profit & Loss
`GET /companies/{ticker}/pl`
Query Params: `from_year`, `to_year`
Returns historical P&L statements.

### 5. Balance Sheet
`GET /companies/{ticker}/bs`
Query Params: `from_year`, `to_year`
Returns historical Balance Sheets.

### 6. Cash Flow
`GET /companies/{ticker}/cashflow`
Query Params: `from_year`, `to_year`
Returns historical Cash Flow statements.

### 7. Financial Ratios
`GET /companies/{ticker}/ratios`
Query Params: `year`
Returns historical financial ratios and analysis KPIs.

### 8. Tearsheet
`GET /companies/{ticker}/tearsheet`
Returns the PDF tearsheet for the company.

### 9. Screener
`GET /screener`
Query Params: `min_roe`, `max_de`, `min_fcf`, `sector`, `min_rev_cagr_5yr`, `min_pat_cagr_5yr`, `max_pe`
Returns companies matching the criteria.

### 10. Sectors
`GET /sectors`
Returns aggregated stats for all 11 sectors.

### 11. Sector Companies
`GET /sectors/{sector}/companies`
Returns all companies in a specific sector.

### 12. Peer Group
`GET /peers/{group_name}`
Returns all companies in a peer group with percentile ranks.

### 13. Peer Compare
`GET /companies/{ticker}/peers/compare`
Returns radar chart data comparing a company against its peer group.

### 14. Market Cap / Valuation
`GET /market-cap/{ticker}`
Returns historical valuation multiples.

### 15. Portfolio Stats
`GET /portfolio/stats`
Returns percentile distributions of KPIs across the portfolio.

### 16. Documents
`GET /companies/{ticker}/documents`
Returns links to annual reports and documents.
