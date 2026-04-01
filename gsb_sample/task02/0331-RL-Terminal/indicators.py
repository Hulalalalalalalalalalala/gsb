import numpy as np
import pandas as pd


def rolling_volatility(prices, window=20, annualize_days=252):
    log_returns = np.log(prices / prices.shift(1)).dropna()
    vol = log_returns.rolling(window=window).std() * np.sqrt(annualize_days)
    return vol


def bollinger_bands(prices, window=20, num_std=2):
    middle = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper = middle + num_std * std
    lower = middle - num_std * std
    return pd.DataFrame({
        "BB_Upper": upper,
        "BB_Middle": middle,
        "BB_Lower": lower
    })
