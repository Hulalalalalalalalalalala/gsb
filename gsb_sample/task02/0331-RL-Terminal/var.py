import numpy as np
import pandas as pd


def historical_var(returns, window=252, confidence_level=0.95):
    var_series = returns.rolling(window=window).quantile(1 - confidence_level)
    return var_series


def count_var_violations(returns, var_series):
    aligned_returns = returns.shift(-1)
    
    mask = ~np.isnan(var_series) & ~np.isnan(aligned_returns)
    valid_var = var_series[mask]
    valid_next_returns = aligned_returns[mask]
    
    n_valid = len(valid_var)
    violations = valid_next_returns < valid_var
    n_violations = violations.sum()
    violation_rate = n_violations / n_valid if n_valid > 0 else 0
    
    return {
        "n_valid": n_valid,
        "n_violations": n_violations,
        "violation_rate": violation_rate,
        "violation_dates": violations[violations].index.tolist(),
        "var_series": valid_var,
        "next_day_returns": valid_next_returns,
        "violation_mask": violations
    }
