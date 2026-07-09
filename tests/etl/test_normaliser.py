"""
test_normaliser.py — 35+ unit tests for normalize_year() and normalize_ticker().

20 tests for normalize_year
15 tests for normalize_ticker
"""

import pytest

from src.etl.normaliser import normalize_year, normalize_ticker


# ============================================================
# normalize_year — 20 tests
# ============================================================

class TestNormalizeYear:
    """20 unit tests for the normalize_year() function."""

    # --- Integer inputs (5 tests) ---

    def test_01_four_digit_int(self):
        assert normalize_year(2024) == 2024

    def test_02_four_digit_int_2015(self):
        assert normalize_year(2015) == 2015

    def test_03_four_digit_int_2000(self):
        assert normalize_year(2000) == 2000

    def test_04_four_digit_int_2030(self):
        assert normalize_year(2030) == 2030

    def test_05_two_digit_int(self):
        """24 → 2024 (2-digit year maps to 2000+)."""
        assert normalize_year(24) == 2024

    # --- Float inputs (2 tests) ---

    def test_06_float_whole(self):
        assert normalize_year(2023.0) == 2023

    def test_07_float_truncated(self):
        """2023.7 truncates to 2023."""
        assert normalize_year(2023.7) == 2023

    # --- String: plain year (4 tests) ---

    def test_08_string_four_digit(self):
        assert normalize_year("2024") == 2024

    def test_09_string_four_digit_2019(self):
        assert normalize_year("2019") == 2019

    def test_10_string_two_digit(self):
        assert normalize_year("23") == 2023

    def test_11_string_two_digit_15(self):
        assert normalize_year("15") == 2015

    # --- String: FY prefix (4 tests) ---

    def test_12_fy_four_digit(self):
        assert normalize_year("FY 2024") == 2024

    def test_13_fy_two_digit(self):
        assert normalize_year("FY24") == 2024

    def test_14_fy_lowercase(self):
        assert normalize_year("fy23") == 2023

    def test_15_fy_with_dots(self):
        """F.Y. 2024 → 2024."""
        assert normalize_year("F.Y. 2024") == 2024

    # --- String: FY range (2 tests) ---

    def test_16_fy_range_4_2(self):
        """FY 2023-24 → 2024 (ending year)."""
        assert normalize_year("FY 2023-24") == 2024

    def test_17_fy_range_2_2(self):
        """23-24 → 2024."""
        assert normalize_year("23-24") == 2024

    # --- String: Month prefix (1 test) ---

    def test_18_mar_year(self):
        assert normalize_year("Mar 2024") == 2024

    # --- String: with whitespace (1 test) ---

    def test_19_whitespace(self):
        assert normalize_year("  2021  ") == 2021

    # --- Error cases (1 test) ---

    def test_20_none_raises(self):
        with pytest.raises(ValueError, match="None"):
            normalize_year(None)


# ============================================================
# normalize_ticker — 15 tests
# ============================================================

class TestNormalizeTicker:
    """15 unit tests for the normalize_ticker() function."""

    # --- Already canonical (3 tests) ---

    def test_01_uppercase_ticker(self):
        assert normalize_ticker("RELIANCE") == "RELIANCE"

    def test_02_two_char_ticker(self):
        assert normalize_ticker("LT") == "LT"

    def test_03_ticker_with_ampersand(self):
        assert normalize_ticker("M&M") == "M&M"

    # --- Exchange suffixes (3 tests) ---

    def test_04_dot_ns_suffix(self):
        assert normalize_ticker("RELIANCE.NS") == "RELIANCE"

    def test_05_dash_nse_suffix(self):
        assert normalize_ticker("TCS-NSE") == "TCS"

    def test_06_space_eq_suffix(self):
        assert normalize_ticker("INFY EQ") == "INFY"

    # --- Aliases (4 tests) ---

    def test_07_alias_infosys(self):
        assert normalize_ticker("infosys") == "INFY"

    def test_08_alias_reliance(self):
        assert normalize_ticker("reliance") == "RELIANCE"

    def test_09_alias_tata_motors(self):
        assert normalize_ticker("Tata Motors") == "TATAMOTORS"

    def test_10_alias_hdfcbank(self):
        assert normalize_ticker("hdfcbank") == "HDFCBANK"

    # --- Whitespace/case handling (2 tests) ---

    def test_11_leading_trailing_spaces(self):
        assert normalize_ticker("  SBIN  ") == "SBIN"

    def test_12_mixed_case(self):
        assert normalize_ticker("tCs") == "TCS"

    # --- Special characters (1 test) ---

    def test_13_zero_width_space(self):
        """Zero-width space should be stripped."""
        raw = "RELIANCE\u200b"
        assert normalize_ticker(raw) == "RELIANCE"

    # --- Error cases (2 tests) ---

    def test_14_none_raises(self):
        with pytest.raises(ValueError, match="None"):
            normalize_ticker(None)

    def test_15_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty"):
            normalize_ticker("")