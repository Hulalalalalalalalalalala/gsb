import os
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Optional, Tuple


def winsorize(series: pd.Series, percentile: float) -> pd.Series:
    if percentile <= 0 or percentile >= 0.5:
        return series
    lower = series.quantile(percentile)
    upper = series.quantile(1 - percentile)
    return series.clip(lower, upper)


def calculate_returns(prices: pd.Series, method: str = "simple") -> pd.Series:
    if method == "simple":
        return prices.pct_change().dropna()
    elif method == "log":
        return np.log(prices / prices.shift(1)).dropna()
    else:
        raise ValueError("method must be 'simple' or 'log'")


def load_eth_data() -> Tuple[Optional[pd.DataFrame], str]:
    data_path = os.environ.get("DATA_PATH", "")
    
    if data_path and os.path.exists(data_path):
        try:
            df = pd.read_csv(data_path, index_col=0, parse_dates=True)
            df.index.name = "Date"
            df = df.sort_index()
            df.index = df.index.tz_localize(None)
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            for col in required_cols:
                if col not in df.columns:
                    return None, f"CSV 缺少必要列: {col}"
            return df, f"已加载本地数据: {data_path}"
        except Exception as e:
            return None, f"加载 CSV 失败: {str(e)}"
    
    try:
        eth = yf.Ticker("ETH-USD")
        df = eth.history(period="max")
        df = df[["Open", "High", "Low", "Close", "Volume"]]
        df.index = df.index.tz_localize(None)
        return df, "已加载 Yahoo Finance 在线数据"
    except Exception as e:
        return None, f"网络加载失败: {str(e)}\n\n建议使用离线模式: DATA_PATH=./data/eth_data.csv streamlit run app.py"


def filter_date_range(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    return df.loc[start_date:end_date].copy()
