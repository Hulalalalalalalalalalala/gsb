import pytest
import pandas as pd
import numpy as np

from data_loader import winsorize, calculate_returns
from simulation import simulate_gbm
from var import historical_var, calculate_var_violations
from indicators import rolling_volatility


def test_winsorize_clips_correctly():
    np.random.seed(42)
    data = pd.Series(np.random.normal(0, 1, 1000))
    data[0] = 100
    data[1] = -100
    
    result = winsorize(data, 0.01)
    
    assert result.max() < 100
    assert result.min() > -100
    np.testing.assert_allclose(result.quantile(0.01), result.min(), rtol=1e-3)
    np.testing.assert_allclose(result.quantile(0.99), result.max(), rtol=1e-3)


def test_winsorize_zero_percentile_no_change():
    data = pd.Series([1, 2, 3, 4, 5])
    result = winsorize(data, 0)
    pd.testing.assert_series_equal(result, data)


def test_calculate_simple_returns():
    prices = pd.Series([100, 101, 102, 103])
    returns = calculate_returns(prices, "simple")
    
    assert len(returns) == 3
    np.testing.assert_almost_equal(returns.iloc[0], 0.01)
    np.testing.assert_almost_equal(returns.iloc[1], 1/101)


def test_calculate_log_returns():
    prices = pd.Series([100, 101, 102, 103])
    returns = calculate_returns(prices, "log")
    
    assert len(returns) == 3
    np.testing.assert_almost_equal(returns.iloc[0], np.log(101/100))
    np.testing.assert_almost_equal(returns.iloc[1], np.log(102/101))


def test_var_alignment_correct_shift():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.01, 500))
    var_series = historical_var(returns, window=250, confidence=0.95)
    result = calculate_var_violations(returns, var_series)
    
    assert result["有效样本长度"] == 250
    assert len(var_series.dropna()) == 251
    assert result["违规笔数"] >= 0
    assert 0 <= result["违规率"] <= 1


def test_simulation_substep_scaling():
    S0 = 100
    daily_mu = 0.001
    daily_sigma = 0.02
    
    np.random.seed(42)
    paths_24, _ = simulate_gbm(S0, daily_mu, daily_sigma, days=1, steps_per_day=24, n_paths=1000, seed=42)
    
    np.random.seed(42)
    paths_48, _ = simulate_gbm(S0, daily_mu, daily_sigma, days=1, steps_per_day=48, n_paths=1000, seed=42)
    
    log_returns_24 = np.log(paths_24[:, -1] / S0)
    log_returns_48 = np.log(paths_48[:, -1] / S0)
    
    std_24 = log_returns_24.std()
    std_48 = log_returns_48.std()
    
    np.testing.assert_allclose(std_24, std_48, rtol=0.1)


def test_rolling_volatility_window():
    prices = pd.Series([100 + i for i in range(100)])
    vol = rolling_volatility(prices, window=20)
    
    assert len(vol.dropna()) == 80
    assert pd.isna(vol.iloc[18])
    assert not pd.isna(vol.iloc[19])
