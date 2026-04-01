import pandas as pd


def historical_var(returns: pd.Series, window: int, confidence: float = 0.95) -> pd.Series:
    var_series = returns.rolling(window=window).quantile(1 - confidence)
    return var_series


def calculate_var_violations(returns: pd.Series, var_series: pd.Series) -> tuple[int, int, float]:
    aligned_returns = returns.shift(-1).dropna()
    aligned_var = var_series.dropna()
    common_idx = aligned_returns.index.intersection(aligned_var.index)
    aligned_returns = aligned_returns.loc[common_idx]
    aligned_var = aligned_var.loc[common_idx]

    n = len(common_idx)
    violations = int((aligned_returns < aligned_var).sum())
    violation_rate = float(violations / n) if n > 0 else 0.0
    return n, violations, violation_rate
