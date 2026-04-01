import numpy as np
import pandas as pd
import pytest

from returns import calculate_returns, winsorize
from monte_carlo import simulate_gbm_multi_day
from var import historical_var, count_var_violations
from indicators import rolling_volatility


def test_winsorize_clips_values():
    np.random.seed(42)
    data = pd.Series(np.random.normal(0, 1, 1000))
    data.loc[0] = 100
    data.loc[1] = -100
    
    result = winsorize(data, 0.01, 0.01)
    
    assert result.max() <= data.quantile(0.99) + 1e-10
    assert result.min() >= data.quantile(0.01) - 1e-10
    assert result.max() < 99
    assert result.min() > -99


def test_calculate_returns_simple_vs_log():
    prices = pd.Series([100, 110, 121])
    
    simple_rets = calculate_returns(prices, "simple")
    log_rets = calculate_returns(prices, "log")
    
    assert len(simple_rets) == 2
    assert len(log_rets) == 2
    assert np.isclose(simple_rets.iloc[0], 0.10)
    assert np.isclose(log_rets.iloc[0], np.log(1.1))
    assert np.all(log_rets < simple_rets)


def test_var_window_alignment():
    np.random.seed(42)
    returns = pd.Series(np.random.normal(0, 0.02, 500))
    
    var = historical_var(returns, window=252, confidence_level=0.95)
    
    assert var.first_valid_index() == 251
    
    result = count_var_violations(returns, var)
    assert result["n_valid"] == 500 - 252
    assert result["n_valid"] + 252 <= len(returns)


def test_monte_carlo_substep_scaling():
    S0 = 100
    mu_daily = 0.001
    sigma_daily = 0.02
    
    np.random.seed(42)
    paths_24 = simulate_gbm_multi_day(S0, mu_daily, sigma_daily, 
                                      days=1, steps_per_day=24, n_paths=1000, seed=42)
    
    np.random.seed(42)
    paths_48 = simulate_gbm_multi_day(S0, mu_daily, sigma_daily, 
                                      days=1, steps_per_day=48, n_paths=1000, seed=42)
    
    vol_24 = np.std(np.log(paths_24[-1, :] / S0))
    vol_48 = np.std(np.log(paths_48[-1, :] / S0))
    
    assert np.isclose(vol_24, vol_48, rtol=0.15)
    assert np.isclose(np.mean(paths_24[-1, :]), np.mean(paths_48[-1, :]), rtol=0.05)


def test_monte_carlo_substeps_count():
    S0 = 100
    paths = simulate_gbm_multi_day(S0, 0.001, 0.02, days=5, steps_per_day=24, 
                                   n_paths=100, seed=42)
    
    assert paths.shape[0] == 5 * 24 + 1
    assert paths[0, 0] == S0
    assert paths.shape[1] == 100


def test_rolling_volatility_window():
    prices = pd.Series(np.cumprod(1 + np.random.normal(0, 0.02, 100)))
    
    vol = rolling_volatility(prices, window=20, annualize_days=252)
    
    assert pd.isna(vol.iloc[18])
    assert not pd.isna(vol.iloc[19])
    assert vol.min() >= 0
