"""
normaliser.py — Normalise raw Excel fields into canonical form.

Functions:
    normalize_year(raw)   → int   (fiscal year, e.g. 2024)
    normalize_ticker(raw) → str   (uppercase NSE ticker, e.g. "RELIANCE")
"""

import re
import unicodedata


# ---------------------------------------------------------------------------
# Year normalisation
# ---------------------------------------------------------------------------

# Map common Indian fiscal-year text patterns to integers
_FY_TEXT_MAP = {
    "fy10": 2010, "fy11": 2011, "fy12": 2012, "fy13": 2013,
    "fy14": 2014, "fy15": 2015, "fy16": 2016, "fy17": 2017,
    "fy18": 2018, "fy19": 2019, "fy20": 2020, "fy21": 2021,
    "fy22": 2022, "fy23": 2023, "fy24": 2024, "fy25": 2025,
}

# Regex: "FY 2023-24" or "FY23-24" or "2023-24" → 2024 (ending year)
_FY_RANGE_RE = re.compile(
    r"(?:fy\s*)?"           # optional FY prefix
    r"(\d{2,4})\s*-\s*(\d{2})",  # 2023-24 or 23-24
    re.IGNORECASE,
)

# Regex: "Mar 2024" or "March-24" or "FY 2024" → 2024
_FY_SINGLE_RE = re.compile(
    r"(?:fy\s*)?"
    r"(?:mar(?:ch)?\s*)?"
    r"(\d{4})",
    re.IGNORECASE,
)


def normalize_year(raw) -> int:
    """Convert a raw year value to a canonical 4-digit fiscal year.

    Accepted inputs:
        - int / float  → 2024
        - str "2024"   → 2024
        - str "FY24"   → 2024
        - str "FY 2023-24" → 2024  (ending year of range)
        - str "23-24"  → 2024
        - str "Mar 2024" → 2024
        - str "FY24"   → 2024
        - str "F.Y. 2023-2024" → 2024

    Returns:
        int: 4-digit year (e.g. 2024)

    Raises:
        ValueError: if the year cannot be parsed or is out of range (2000–2030).
    """
    if raw is None:
        raise ValueError("Year value is None")

    # --- numeric path ---
    if isinstance(raw, (int, float)):
        yr = int(raw)
        if 2000 <= yr <= 2030:
            return yr
        # two-digit: 24 → 2024
        if 0 <= yr < 100:
            return 2000 + yr
        raise ValueError(f"Year {raw} out of valid range 2000-2030")

    # --- string path ---
    if not isinstance(raw, str):
        raise ValueError(f"Unsupported year type: {type(raw).__name__}")

    s = unicodedata.normalize("NFKD", raw).strip().lower()
    s = s.replace("\u200b", "")  # zero-width space
    s = re.sub(r"[.\s]+", " ", s)  # collapse dots & spaces

    # 1. Exact match from FY text map (e.g. "fy24")
    if s.replace(" ", "") in _FY_TEXT_MAP:
        return _FY_TEXT_MAP[s.replace(" ", "")]

    # 2. Range pattern: "fy 2023-24" or "23-24"
    m = _FY_RANGE_RE.search(s)
    if m:
        start = int(m.group(1))
        end = int(m.group(2))
        # Resolve 2-digit to 4-digit
        end_full = end if end >= 100 else 2000 + end
        start_full = start if start >= 100 else (2000 + start)
        # If start > end, they span a century boundary
        if start_full > end_full:
            end_full += 100
        return end_full  # fiscal year = ending year

    # 3. Single year: "fy 2024" or "mar 2024"
    m = _FY_SINGLE_RE.search(s)
    if m:
        yr = int(m.group(1))
        if 2000 <= yr <= 2030:
            return yr
        if 0 <= yr < 100:
            return 2000 + yr
        raise ValueError(f"Year '{raw}' parsed to {yr}, out of range 2000-2030")

    # 4. Bare 2-digit: "23" → 2023
    m2 = re.match(r"^(\d{1,2})$", s)
    if m2:
        yr = int(m2.group(1))
        return 2000 + yr

    raise ValueError(f"Cannot parse year from: '{raw}'")


# ---------------------------------------------------------------------------
# Ticker normalisation
# ---------------------------------------------------------------------------

# Known NSE suffixes that should be stripped / mapped
_NS2BSE_SUFFIXES = {
    "nse": "", "bse": "", "eq": "", "bo": "",
    "ns": "", "be": "",
}

# Ticker cleanup regex: remove non-alphanumeric except & and dot
_TICKER_CLEAN_RE = re.compile(r"[^A-Za-z0-9&.]")

# Common ticker aliases (lowercase → canonical)
_TICKER_ALIASES = {
    "infy": "INFY", "infosys": "INFY",
    "reli": "RELIANCE", "reliance": "RELIANCE", "rel": "RELIANCE",
    "tcs": "TCS",
    "hdfcbank": "HDFCBANK", "hdfc": "HDFCBANK",
    "icicibank": "ICICIBANK", "icici": "ICICIBANK",
    "sbin": "SBIN", "sbi": "SBIN",
    "bharti": "BHARTIARTL", "airtel": "BHARTIARTL",
    "itc": "ITC",
    "kotak": "KOTAKBANK", "kmb": "KOTAKBANK",
    "lt": "LT", "larsen": "LT",
    "hul": "HINDUNILVR", "hindustan unilever": "HINDUNILVR",
    "axisbank": "AXISBANK", "axis": "AXISBANK",
    "bajfin": "BAJFINANCE", "bajajf": "BAJFINANCE",
    "maruti": "MARUTI", "m&m": "M&M", "mm": "M&M",
    "asianpain": "ASIANPAINT", "asian paint": "ASIANPAINT",
    "sunpharma": "SUNPHARMA", "sun": "SUNPHARMA",
    "tatasteel": "TATASTEEL", "tsteel": "TATASTEEL",
    "wipro": "WIPRO",
    "hcltech": "HCLTECH",
    "ongc": "ONGC",
    "ntpc": "NTPC",
    "powergrid": "POWERGRID", "pgcil": "POWERGRID",
    "coalindia": "COALINDIA",
    "nios": "NIACL",
    "hindalco": "HINDALCO",
    "tata motors": "TATAMOTORS", "tatam": "TATAMOTORS",
    "adani ports": "ADANIPORTS", "adaniports": "ADANIPORTS",
    "techm": "TECHM", "mahindra satyam": "TECHM",
    "drreddy": "DRREDDY", "dr reddy": "DRREDDY",
    "cipla": "CIPLA",
    "bpcl": "BPCL",
    "hpcl": "HPCL",
    "indusind": "INDUSINDBK",
    "divislab": "DIVISLAB",
    "grasim": "GRASIM",
    "ultracemco": "ULTRACEMCO", "acc": "ULTRACEMCO",
    "ambujacem": "AMBUJACEM",
    "dabur": "DABUR",
    "britannia": "BRITANNIA",
    "hero": "HEROMOTOCO", "heromotocorp": "HEROMOTOCO",
    "eicher": "EICHERMOT", "eichermotor": "EICHERMOT",
    "muthoot": "MUTHOOTFIN",
    "bajajfinsv": "BAJAJFINSV",
    "titan": "TITAN",
    "marico": "MARICO",
    "vedl": "VEDL", "vedanta": "VEDL",
    "jspl": "JSPL", "jindal steel": "JSPL",
    "nalco": "NALCO",
    "nhpc": "NHPC",
    "nmdc": "NMDC",
    "power corp": "POWERINDIA",
    "sail": "SAIL",
    "unionbank": "UNIONBANK",
    "bankbaroda": "BANKBARODA", "bob": "BANKBARODA",
    "canbank": "CANBK", "canara": "CANBK",
    "pnb": "PNB", "punjab": "PNB",
    "indianbank": "INDIANB",
    "federal": "FEDERALBNK",
    "idfc": "IDFCFIRSTB",
    "bandhan": "BANDHANBNK",
    "hdfclife": "HDFCLIFE",
    "sbilife": "SBILIFE",
    "icicipru": "ICICIPRULI",
    "kotakbank": "KOTAKBANK",
    "maxlife": "MAXLIFE",  # not in N100, kept for safety
    "tornipharm": "TORNTPHARM", "tornt": "TORNTPHARM",
    "alkem": "ALKEM",
    "lalpath": "LALPATHLAB",
    "delhivery": "DELHIVERY",
    "nykaa": "NYKAA", "fsn ecom": "NYKAA",
    "zomato": "ZOMATO",
    "paytm": "PAYTM",
    "pb fintech": "PBBFINTECH",
    "adani ent": "ADANIENT", "adanienterprises": "ADANIENT",
    "tatapower": "TATAPOWER",
    "tataelxsi": "TATAELXSI",
    "tcs": "TCS",
    "wipro": "WIPRO",
    "hcltech": "HCLTECH",
    "l&t": "LT",
    "m&m fin": "M&MFIN",
    "shreecement": "SHREECEM",
    "bajaj auto": "BAJAJAUTO",
    "godrejcp": "GODREJCP",
    "pidilite": "PIDILITIND",
    "volex": "VOLTAS",
    "havells": "HAVELLS",
    "aarti": "AARTIIND",
    "astral": "ASTRAL",
    "lupin": "LUPIN",
    "apollo": "APOLLOHOSP",
    "max health": "MAXHEALTH",
    "fortis": "FORTIS",
    "devyani": "DEVYANI",
    "oberoi": "OBEROIRLTY",
    "indianhotel": "INDIANHOTL",
    "ejhermahld": "EIHOTEL",
    "chalet": "CHALET",
    "tvsmotor": "TVSMOTOR",
    "bajaj hold": "BAJAJHLDNG",
    "cipla": "CIPLA",
    "sunpharma": "SUNPHARMA",
    "drreddy": "DRREDDY",
    "divislab": "DIVISLAB",
    "alkem": "ALKEM",
    "lupin": "LUPIN",
    "cipla": "CIPLA",
    "biocon": "BIOCON",
    "zydus": "ZYDUSLIFE",
    "glaxo": "GLAXO",
    "abbott": "ABBOTINDIA",
    "torrent": "TORNTPOWER",
}


def normalize_ticker(raw) -> str:
    """Convert a raw ticker value to a canonical uppercase NSE ticker.

    Accepted inputs:
        - "RELIANCE"           → "RELIANCE"
        - "reliance"           → "RELIANCE"
        - "RELIANCE.NS"        → "RELIANCE"
        - "RELIANCE-EQ"        → "RELIANCE"
        - "RELIANCE NSE"       → "RELIANCE"
        - "Reliance Industries" → "RELIANCE"  (via alias)
        - "INFY"               → "INFY"
        - "INFOSYS"            → "INFY"       (via alias)
        - "TATA MOTORS LTD"    → "TATAMOTORS" (via alias)
        - "M & M"              → "M&M"
        - "  sbin  "           → "SBIN"

    Returns:
        str: Uppercase ticker, e.g. "RELIANCE"

    Raises:
        ValueError: if ticker is None, empty, or unresolvable.
    """
    if raw is None:
        raise ValueError("Ticker value is None")

    if not isinstance(raw, str):
        raw = str(raw).strip()

    s = raw.strip()
    if not s:
        raise ValueError("Ticker is empty string")

    # Normalise unicode
    s = unicodedata.normalize("NFKD", s)
    # Remove zero-width chars
    s = s.replace("\u200b", "").replace("\ufeff", "")

    # Strip known exchange suffixes: .NS, .BO, -NSE, -EQ, etc.
    s_lower = s.lower()
    for suffix in sorted(_NS2BSE_SUFFIXES.keys(), key=len, reverse=True):
        # Dot prefix like ".NS" or ".NSE"
        if s_lower.endswith("." + suffix):
            s = s[: -(len(suffix) + 1)]
            s_lower = s.lower()
        # Dash prefix like "-NSE" or "-EQ"
        elif s_lower.endswith("-" + suffix):
            s = s[: -(len(suffix) + 1)]
            s_lower = s.lower()
        # Space prefix like " NSE"
        elif s_lower.endswith(" " + suffix):
            s = s[: -(len(suffix) + 1)]
            s_lower = s.lower()

    # Remove any remaining non-alphanumeric (preserve & and .)
    s = _TICKER_CLEAN_RE.sub("", s).strip()

    if not s:
        raise ValueError(f"Ticker '{raw}' resolved to empty after cleaning")

    # Check aliases (case-insensitive)
    alias_key = s.lower().replace(" ", "").replace("&", "")
    if alias_key in _TICKER_ALIASES:
        return _TICKER_ALIASES[alias_key]

    # Uppercase and return
    return s.upper().strip()