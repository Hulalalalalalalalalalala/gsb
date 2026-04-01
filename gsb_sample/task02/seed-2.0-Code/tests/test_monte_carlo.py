import pytest
import numpy as np
import pandas as pd
from src.monte_carlo import estimate_gbm_params, simulate_gbm, get_terminal_returns, get_terminal_quantiles


def test_estimate_gbm_params():
    np.random.seed(42)
    daily_returns = pd.Series(np.random.normal(0.001, 0.02, 252))
    mu, sigma = estimate_gbm_params(daily_returns, annualize_days=252)
    assert isinstance(mu, float)
    assert isinstance(sigma, float)
    assert sigma > 0


def test_simulate_gbm_substeps():
    substep_indices, paths = simulate_gbm(
        S0=100,
        mu=0.1,
        sigma=0.2,
        horizon_days=1,
        substeps_per_day=24,
        num_paths=10,
        random_seed=42
    )
    assert len(substep_indices) == 25
    assert paths.shape == (25, 10)
    assert (paths[0, :] == 100).all()


def test_simulate_gbm_substep_scaling():
    substep_indices_24, paths_24 = simulate_gbm(
        S0=100,
        mu=0.1,
        sigma=0.2,
        horizon_days=1,
        substeps_per_day=24,
        num_paths=1000,
        random_seed=42
    )
    substep_indices_48, paths_48 = simulate_gbm(
        S0=100,
        mu=0.1,
        sigma=0.2,
        horizon_days=1,
        substeps_per_day=48,
        num_paths=1000,
        random_seed=43
    )
    returns_24 = (paths_24[-1, :] - 100) / 100
    returns_48 = (paths_48[-1, :] - 100) / 100
    assert abs(returns_24.std() - returns_48.std()) < 0.02


def test_get_terminal_returns():
    paths = np.array([[100, 100, 100], [110, 105, 90]])
    simple_returns = get_terminal_returns(paths, method="simple")
    log_returns = get_terminal_returns(paths, method="log")
    assert np.allclose(simple_returns, np.array([0.1, 0.05, -0.1]))
    assert np.allclose(log_returns, np.log(np.array([1.1, 1.05, 0.9])))


def test_get_terminal_quantiles():
    terminal_values = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    quantiles = get_terminal_quantiles(terminal_values, quantiles=[0.1, 0.5, 0.9])
    assert quantiles["10%"] == pytest.approx(1.9)
    assert quantiles["50%"] == pytest.approx(5.5)
    assert quantiles["90%"] == pytest.approx(9.1)
