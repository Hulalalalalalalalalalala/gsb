import numpy as np
import pandas as pd


def estimate_gbm_parameters(returns: pd.Series, annualization_factor: int = 252) -> dict:
    """
    估计GBM参数
    日频漂移和波动，年化通过乘以 annualization_factor 得到
    """
    daily_mu = returns.mean()
    daily_sigma = returns.std(ddof=1)
    
    return {
        "daily_mu": daily_mu,
        "daily_sigma": daily_sigma,
        "annual_mu": daily_mu * annualization_factor,
        "annual_sigma": daily_sigma * np.sqrt(annualization_factor)
    }


def simulate_gbm(
    S0: float,
    daily_mu: float,
    daily_sigma: float,
    days: int,
    steps_per_day: int = 24,
    n_paths: int = 1000,
    seed: int = 42
) -> tuple:
    """
    几何布朗运动模拟
    每个交易日拆分成 steps_per_day 个子步
    每个子步都有独立的随机扰动
    """
    np.random.seed(seed)
    
    dt = 1.0 / steps_per_day
    total_steps = days * steps_per_day
    
    Z = np.random.normal(0, 1, size=(n_paths, total_steps))
    
    drift = (daily_mu - 0.5 * daily_sigma**2) * dt
    diffusion = daily_sigma * np.sqrt(dt)
    
    log_returns = drift + diffusion * Z
    log_paths = np.cumsum(log_returns, axis=1)
    
    paths = S0 * np.exp(log_paths)
    
    step_indices = np.arange(total_steps)
    
    return paths, step_indices


def calculate_quantiles(paths: np.ndarray, quantiles: list = [0.01, 0.05, 0.5, 0.95, 0.99]) -> pd.DataFrame:
    final_prices = paths[:, -1]
    results = []
    for q in quantiles:
        results.append({
            "分位数": f"{int(q*100)}%",
            "终点价格": np.quantile(final_prices, q)
        })
    return pd.DataFrame(results)
