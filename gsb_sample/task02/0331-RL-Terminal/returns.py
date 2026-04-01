import numpy as np
import pandas as pd
from scipy import stats


def calculate_returns(prices, method="log"):
    if method == "simple":
        return prices.pct_change().dropna()
    elif method == "log":
        return np.log(prices / prices.shift(1)).dropna()
    else:
        raise ValueError(f"Unknown return method: {method}")


def winsorize(series, lower_pct=0.01, upper_pct=0.01):
    lower = series.quantile(lower_pct)
    upper = series.quantile(1 - upper_pct)
    return series.clip(lower=lower, upper=upper)


def calculate_statistics(returns_series):
    returns_array = returns_series.dropna().values
    return {
        "n_samples": len(returns_array),
        "mean": np.mean(returns_array),
        "variance": np.var(returns_array, ddof=1),
        "skewness": stats.skew(returns_array),
        "kurtosis": stats.kurtosis(returns_array),
        "jb_stat": stats.jarque_bera(returns_array)[0],
        "jb_pvalue": stats.jarque_bera(returns_array)[1]
    }


def rolling_skewness(returns_series, window=21):
    return returns_series.rolling(window=window).skew()


def rolling_kurtosis(returns_series, window=21):
    return returns_series.rolling(window=window).apply(
        lambda x: stats.kurtosis(x), raw=True
    )
