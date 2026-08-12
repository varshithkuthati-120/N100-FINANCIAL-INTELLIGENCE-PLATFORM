import pytest
import pandas as pd
from src.dq.rules import check_dq_rules

class TestDQRules:
    
    def _create_df(self, **kwargs):
        base = {
            'roe': 15.0, 'equity': 100, 'sales': 100, 'total_assets': 500,
            'total_liab': 200, 'cfo': 50, 'debt_to_equity': 1.0, 'current_ratio': 1.5,
            'interest_cov': 5.0, 'pe_ratio': 20.0, 'pb_ratio': 3.0, 'opm': 20.0, 'tax': 10.0
        }
        base.update(kwargs)
        return pd.DataFrame([base])

    def test_dq01_missing_roe(self):
        df = self._create_df(roe=None)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ01'
        assert violations[0]['severity'] == 'MEDIUM'
        
    def test_dq02_negative_equity(self):
        df = self._create_df(equity=-50)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ02'
        
    def test_dq03_sales_zero(self):
        df = self._create_df(sales=0)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ03'
        
    def test_dq04_assets_lt_liab(self):
        df = self._create_df(total_assets=100, total_liab=200)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ04'
        
    def test_dq05_missing_cfo(self):
        df = self._create_df(cfo=None)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ05'
        
    def test_dq06_high_de(self):
        df = self._create_df(debt_to_equity=11.0)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ06'
        
    def test_dq07_low_current_ratio(self):
        df = self._create_df(current_ratio=0.4)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ07'
        
    def test_dq08_negative_sales(self):
        df = self._create_df(sales=-10)
        violations = check_dq_rules(df)
        # Would also trigger DQ03, so we check if DQ08 is present
        rule_ids = [v['rule_id'] for v in violations]
        assert 'DQ08' in rule_ids
        
    def test_dq09_negative_interest_cov(self):
        df = self._create_df(interest_cov=-1.0)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ09'
        
    def test_dq10_missing_pe(self):
        df = self._create_df(pe_ratio=None)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ10'
        
    def test_dq11_missing_pb(self):
        df = self._create_df(pb_ratio=None)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ11'
        
    def test_dq12_zero_assets(self):
        df = self._create_df(total_assets=0)
        violations = check_dq_rules(df)
        rule_ids = [v['rule_id'] for v in violations]
        assert 'DQ12' in rule_ids
        
    def test_dq13_high_opm(self):
        df = self._create_df(opm=150.0)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ13'
        
    def test_dq14_negative_tax(self):
        df = self._create_df(tax=-50.0)
        violations = check_dq_rules(df)
        assert len(violations) == 1
        assert violations[0]['rule_id'] == 'DQ14'
