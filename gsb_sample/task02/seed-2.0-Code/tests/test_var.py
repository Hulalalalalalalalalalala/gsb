import pytest
import pandas as pd
import numpy as np
from src.var import historical_var, calculate_var_violations


def test_historical_var():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.01, 100))
    var_series = historical_var(returns, window=20, confidence=0.95)
    assert len(var_series) == 100
    assert var_series.iloc[:19].isna().all()


def test_calculate_var_violations():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.01, 100), index=pd.date_range("2024-01-01", periods=100))
    var_series = historical_var(returns, window=20, confidence=0.95)
    n_valid, n_violations, violation_rate = calculate_var_violations(returns, var_series)
    assert n_valid == 80
    assert isinstance(n_violations, int)
    assert 0 <= violation_rate <= 1
