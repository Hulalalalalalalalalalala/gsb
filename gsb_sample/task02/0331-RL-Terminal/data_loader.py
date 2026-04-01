import os
import pandas as pd
import streamlit as st
import warnings

warnings.filterwarnings("ignore")

SYMBOL_YF = "ETH-USD"


def _load_ohlcv_csv(path):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        df = df.copy()
        df.index = df.index.tz_convert("UTC").tz_localize(None)
    cols = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"missing columns: {missing}")
    return df[cols].copy()


def _fetch_ohlcv_from_web():
    import yfinance as yf
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


@st.cache_data(show_spinner="Loading OHLCV data...")
def load_ohlcv(use_local_csv=True):
    p = os.environ.get("ETH_BASELINE_DATA")
    if use_local_csv and p:
        try:
            return _load_ohlcv_csv(p)
        except Exception as e:
            st.warning(f"Failed to load local CSV: {e}. Falling back to online source.")
    
    try:
        return _fetch_ohlcv_from_web()
    except Exception as e:
        st.error(f"""
        ❌ Failed to fetch online data: {str(e)}
        
        **Please use offline CSV mode:**
        1. Prepare a CSV file with Date index and columns: Open, High, Low, Close, Volume
        2. Set environment variable: `ETH_BASELINE_DATA=/path/to/your/data.csv`
        3. Restart the app
        """)
        st.stop()


@st.cache_data
def filter_by_date(df, start_date, end_date):
    mask = (df.index.date >= start_date) & (df.index.date <= end_date)
    return df[mask].copy()
