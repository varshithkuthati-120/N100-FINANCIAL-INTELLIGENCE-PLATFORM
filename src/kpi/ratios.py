import numpy as np

def calculate_roe(net_profit, equity):
    if equity <= 0:
        return None
    return (net_profit / equity) * 100

def calculate_de(total_debt, equity):
    if total_debt == 0:
        return 0.0
    if equity <= 0:
        return None
    return total_debt / equity

def calculate_icr(op_profit, interest):
    if interest == 0:
        return None
    return op_profit / interest

def check_de_flag(de, is_financial):
    if not is_financial and de is not None and de > 5.0:
        return True
    return False

def calculate_cagr(start_val, end_val, periods):
    if start_val < 0 and end_val > 0:
        return "TURNAROUND"
    if start_val > 0 and end_val < 0:
        return "DECLINE_TO_LOSS"
    if start_val <= 0 or end_val <= 0 or periods <= 0:
        return None
    return ((end_val / start_val) ** (1/periods) - 1) * 100

def check_opm_divergence(reported_opm, calculated_opm):
    if reported_opm is None or calculated_opm is None:
        return False
    return abs(reported_opm - calculated_opm) > 5.0

def calculate_cfo_quality(cfo_list, pat_list):
    ratios = []
    for cfo, pat in zip(cfo_list, pat_list):
        if pat == 0:
            continue
        ratios.append(cfo / pat)
    if not ratios:
        return None
    return sum(ratios) / len(ratios)
