import numpy as np
import pandas as pd


def estimate_gbm_params(returns: pd.Series, annualize_days: int = 252) -> tuple[float, float]:
    mu = returns.mean() * annualize_days
    sigma = returns.std() * np.sqrt(annualize_days)
    return mu, sigma


def simulate_gbm(
    S0: float,
    mu: float,
    sigma: float,
    horizon_days: int,
    substeps_per_day: int,
    num_paths: int,
    random_seed: int
) -> tuple[np.ndarray, np.ndarray]:
    np.random.seed(random_seed)
    total_substeps = horizon_days * substeps_per_day
    dt = 1.0 / (252 * substeps_per_day)
    drift = (mu - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt)

    log_returns = drift + diffusion * np.random.normal(0, 1, (total_substeps, num_paths))
    log_paths = np.cumsum(log_returns, axis=0)
    paths = S0 * np.exp(log_paths)
    paths = np.vstack([np.full(num_paths, S0), paths])
    substep_indices = np.arange(0, total_substeps + 1)
    return substep_indices, paths


def get_terminal_returns(paths: np.ndarray, method: str = "simple") -> np.ndarray:
    S0 = paths[0, 0]
    ST = paths[-1, :]
    if method == "simple":
        returns = (ST - S0) / S0
    else:
        returns = np.log(ST / S0)
    return returns


def get_terminal_quantiles(terminal_values: np.ndarray, quantiles: list[float] = [0.01, 0.05, 0.5, 0.95, 0.99]) -> dict:
    results = {}
    for q in quantiles:
        results[f"{int(q*100)}%"] = np.quantile(terminal_values, q)
    return results
