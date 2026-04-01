import pytest
import pandas as pd
import numpy as np
from src.metrics import calculate_returns, winsorize, rolling_volatility, bollinger_bands, distribution_stats


def test_calculate_returns_simple():
    prices = pd.Series([100, 110, 105, 120], index=pd.date_range("2024-01-01", periods=4))
    returns = calculate_returns(prices, method="simple")
    expected = pd.Series([0.1, -0.0454545, 0.1428571], index=prices.index[1:])
    pd.testing.assert_series_equal(returns, expected, atol=1e-6)


def test_calculate_returns_log():
    prices = pd.Series([100, 110, 105, 120], index=pd.date_range("2024-01-01", periods=4))
    returns = calculate_returns(prices, method="log")
    expected = pd.Series([np.log(1.1), np.log(105/110), np.log(120/105)], index=prices.index[1:])
    pd.testing.assert_series_equal(returns, expected, atol=1e-6)


def test_winsorize():
    series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])
    winsorized = winsorize(series, lower=0.1, upper=0.1)
    assert winsorized.min() >= 1.8
    assert winsorized.max() <= 20.0


def test_rolling_volatility():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.01, 100))
    vol = rolling_volatility(returns, window=20, annualize_days=252)
    assert len(vol) == 100
    assert vol.iloc[:19].isna().all()


def test_bollinger_bands():
    prices = pd.Series([100] * 30)
    bb = bollinger_bands(prices, window=20)
    assert "SMA" in bb.columns
    assert "Upper" in bb.columns
    assert "Lower" in bb.columns
    pd.testing.assert_series_equal(bb["SMA"].iloc[19:], pd.Series([100.0] * 11, index=prices.index[19:], name="SMA"))


def test_distribution_stats():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.01, 1000))
    stats = distribution_stats(returns)
    assert stats["sample_size"] == 1000
    assert abs(stats["mean"]) < 0.01
    assert abs(stats["skewness"]) < 0.5
    assert abs(stats["kurtosis"]) < 1.0
