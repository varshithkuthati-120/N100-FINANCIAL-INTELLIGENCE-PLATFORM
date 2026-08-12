import pytest
from src.kpi.ratios import (
    calculate_roe, calculate_de, calculate_icr, check_de_flag,
    calculate_cagr, check_opm_divergence, calculate_cfo_quality
)

class TestRatios:
    # ROE Tests (4)
    def test_roe_positive_equity(self):
        assert calculate_roe(100, 500) == 20.0
        
    def test_roe_negative_equity(self):
        assert calculate_roe(100, -50) is None
        
    def test_roe_zero_equity(self):
        assert calculate_roe(100, 0) is None
        
    def test_roe_negative_profit(self):
        assert calculate_roe(-50, 500) == -10.0

    # D/E Tests (4)
    def test_de_debt_free(self):
        assert calculate_de(0, 1000) == 0.0
        
    def test_de_normal(self):
        assert calculate_de(500, 1000) == 0.5
        
    def test_de_negative_equity(self):
        assert calculate_de(500, -100) is None
        
    def test_de_zero_equity(self):
        assert calculate_de(500, 0) is None
        
    # ICR Tests (3)
    def test_icr_zero_interest(self):
        assert calculate_icr(1000, 0) is None
        
    def test_icr_normal(self):
        assert calculate_icr(1000, 100) == 10.0
        
    def test_icr_negative_profit(self):
        assert calculate_icr(-500, 100) == -5.0
        
    # D/E Flag Tests (2)
    def test_de_flag_non_financial_high(self):
        assert check_de_flag(6.0, False) is True
        
    def test_de_flag_financial_high(self):
        assert check_de_flag(6.0, True) is False
        
    # CAGR Tests (4)
    def test_cagr_turnaround(self):
        assert calculate_cagr(-100, 50, 5) == "TURNAROUND"
        
    def test_cagr_decline_to_loss(self):
        assert calculate_cagr(100, -50, 5) == "DECLINE_TO_LOSS"
        
    def test_cagr_normal(self):
        assert round(calculate_cagr(100, 161.051, 5), 2) == 10.0
        
    def test_cagr_zero_start(self):
        assert calculate_cagr(0, 100, 5) is None

    # OPM Divergence Tests (2)
    def test_opm_divergence_true(self):
        assert check_opm_divergence(10.0, 16.0) is True
        
    def test_opm_divergence_false(self):
        assert check_opm_divergence(10.0, 11.0) is False

    # CFO Quality Tests (1)
    def test_cfo_quality_calculation(self):
        assert calculate_cfo_quality([100, 200, 150], [50, 100, 75]) == 2.0
