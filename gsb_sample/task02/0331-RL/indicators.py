import pandas as pd
import numpy as np


def rolling_volatility(prices: pd.Series, window: int, annualization_factor: int = 252) -> pd.Series:
    log_returns = np.log(prices / prices.shift(1)).dropna()
    return log_returns.rolling(window=window).std() * np.sqrt(annualization_factor)


def bollinger_bands(prices: pd.Series, window: int, num_std: float = 2.0) -> pd.DataFrame:
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper = sma + num_std * std
    lower = sma - num_std * std
    
    return pd.DataFrame({
        "BB_Mid": sma,
        "BB_Upper": upper,
        "BB_Lower": lower
    }, index=prices.index)
