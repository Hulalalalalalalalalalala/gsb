import os
import pandas as pd
import yfinance as yf

SYMBOL_YF = "ETH-USD"


def load_ohlcv_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        df = df.copy()
        df.index = df.index.tz_convert("UTC").tz_localize(None)
    cols = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"missing columns: {missing}")
    return df[cols].copy()


def fetch_ohlcv_from_yahoo() -> pd.DataFrame:
    tkr = yf.Ticker(SYMBOL_YF)
    raw = tkr.history(period="5y", interval="1d", auto_adjust=True)
    if raw is None or raw.empty:
        raise RuntimeError("no rows from yfinance (check network or symbol)")
    df = raw.dropna(how="any")
    cols = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"missing columns: {missing}")
    return df[cols].copy()


def load_ohlcv() -> tuple[pd.DataFrame, str]:
    csv_path = os.environ.get("ETH_BASELINE_DATA")
    if csv_path:
        try:
            return load_ohlcv_csv(csv_path), "local"
        except Exception as e:
            raise RuntimeError(f"Failed to load local CSV: {e}")
    try:
        return fetch_ohlcv_from_yahoo(), "yahoo"
    except Exception as e:
        raise RuntimeError(f"Failed to fetch from Yahoo Finance: {e}")
