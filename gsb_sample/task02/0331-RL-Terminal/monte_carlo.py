import numpy as np
import pandas as pd


def estimate_gbm_parameters(prices, annualize_days=252, use_recent_days=None):
    if use_recent_days is not None:
        prices = prices.tail(use_recent_days)
    
    log_returns = np.log(prices / prices.shift(1)).dropna()
    n = len(log_returns)
    
    mu_daily = np.mean(log_returns)
    sigma_daily = np.std(log_returns, ddof=1)
    
    mu_annual = mu_daily * annualize_days
    sigma_annual = sigma_daily * np.sqrt(annualize_days)
    
    return {
        "mu_daily": mu_daily,
        "sigma_daily": sigma_daily,
        "mu_annual": mu_annual,
        "sigma_annual": sigma_annual,
        "n_days": n
    }


def simulate_gbm_multi_day(S0, mu_daily, sigma_daily, days=1, steps_per_day=24, 
                           n_paths=1000, seed=42):
    np.random.seed(seed)
    
    total_steps = days * steps_per_day
    dt = 1.0 / steps_per_day
    
    drift = (mu_daily - 0.5 * sigma_daily**2) * dt
    diffusion = sigma_daily * np.sqrt(dt)
    
    Z = np.random.normal(0, 1, size=(total_steps, n_paths))
    log_increments = drift + diffusion * Z
    
    log_paths = np.log(S0) + np.cumsum(log_increments, axis=0)
    paths = np.exp(log_paths)
    
    paths = np.vstack([np.full(n_paths, S0), paths])
    
    return paths


def get_endpoint_quantiles(paths, quantiles=[0.01, 0.05, 0.5, 0.95, 0.99]):
    endpoints = paths[-1, :]
    endpoint_returns = (endpoints - paths[0, 0]) / paths[0, 0]
    
    result = {}
    for q in quantiles:
        price_q = np.quantile(endpoints, q)
        ret_q = np.quantile(endpoint_returns, q)
        result[q] = {"price": price_q, "return": ret_q}
    
    return result, endpoints, endpoint_returns
