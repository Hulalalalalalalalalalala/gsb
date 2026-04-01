import numpy as np
import pandas as pd
from scipy import stats


def calculate_returns(prices: pd.Series, method: str = "simple") -> pd.Series:
    if method == "simple":
        returns = prices.pct_change().dropna()
    elif method == "log":
        returns = np.log(prices / prices.shift(1)).dropna()
    else:
        raise ValueError("method must be 'simple' or 'log'")
    return returns


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.01) -> pd.Series:
    lower_val = series.quantile(lower)
    upper_val = series.quantile(1 - upper)
    return series.clip(lower=lower_val, upper=upper_val)


def rolling_volatility(returns: pd.Series, window: int = 20, annualize_days: int = 252) -> pd.Series:
    return returns.rolling(window=window).std() * np.sqrt(annualize_days)


def bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.DataFrame:
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    return pd.DataFrame({"SMA": sma, "Upper": upper, "Lower": lower})


def distribution_stats(returns: pd.Series) -> dict:
    n = len(returns)
    mean = returns.mean()
    var = returns.var()
    skew = returns.skew()
    kurt = returns.kurtosis()
    jb_stat, jb_pvalue = stats.jarque_bera(returns)
    return {
        "sample_size": n,
        "mean": mean,
        "variance": var,
        "skewness": skew,
        "kurtosis": kurt,
        "jb_statistic": jb_stat,
        "jb_pvalue": jb_pvalue
    }


def rolling_skewness(returns: pd.Series, window: int = 20) -> pd.Series:
    return returns.rolling(window=window).skew()


def rolling_kurtosis(returns: pd.Series, window: int = 20) -> pd.Series:
    return returns.rolling(window=window).kurtosis()
