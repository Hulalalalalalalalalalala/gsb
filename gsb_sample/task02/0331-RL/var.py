import pandas as pd
import numpy as np


def historical_var(returns: pd.Series, window: int, confidence: float = 0.95) -> pd.Series:
    """
    滚动窗口历史VaR
    用窗口内的历史分位数预测下一日
    VaR为负数表示损失
    """
    var_series = returns.rolling(window=window).quantile(1 - confidence)
    return var_series


def calculate_var_violations(returns: pd.Series, var_series: pd.Series) -> dict:
    """
    计算VaR违规次数和违规率
    VaR预测下一日，所以需要对齐：var[t] 预测 returns[t+1]
    """
    aligned_returns = returns.shift(-1)
    
    valid_mask = var_series.notna() & aligned_returns.notna()
    var_valid = var_series[valid_mask]
    returns_valid = aligned_returns[valid_mask]
    
    violations = returns_valid < var_valid
    n_violations = violations.sum()
    n_valid = len(var_valid)
    violation_rate = n_violations / n_valid if n_valid > 0 else 0
    
    return {
        "有效样本长度": n_valid,
        "违规笔数": n_violations,
        "违规率": violation_rate,
        "预期违规率": 1 - 0.95,
        "VaR序列": var_series,
        "收益序列": returns,
        "违规标记": violations
    }
