# ETH baseline — 故意写成「一把梭」单文件，后续留给评测做重构/扩展
# 行为：拉取约 5 年日线，仅输出一张 K 线图 PNG

import os
import warnings

warnings.filterwarnings("ignore")

SYMBOL_YF = "ETH-USD"  # Yahoo Finance 代码
YEARS_WANTED = 5  # 名义上 5 年；下面 yfinance 用 period="5y" 偷懒对齐

# 这些路径写死，后面评测可要求改成 argparse / 配置
OUT_PNG = "eth_candles.png"
STYLE_OVERRIDE = "charles"  # mplfinance 主题，暂时未暴露 CLI


def _load_ohlcv_csv(path):
    """从 CSV 读入（供脱网/被 Yahoo 限频时自测；非真实行情）。"""
    import pandas as pd

    df = pd.read_csv(path, index_col=0, parse_dates=True)
    if isinstance(df.index, pd.DatetimeIndex) and df.index.tz is not None:
        df = df.copy()
        df.index = df.index.tz_convert("UTC").tz_localize(None)
    cols = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"missing columns: {missing}")
    return df[cols].copy()


def fetch_ohlcv_from_web():
    """网络拉取；失败时无重试、无日志级别，结构简陋。"""
    import yfinance as yf

    tkr = yf.Ticker(SYMBOL_YF)
    # interval=1d 日线；auto_adjust=True 让 OHLC 与分红拆分对齐（加密基本无影响）
    raw = tkr.history(period="5y", interval="1d", auto_adjust=True)
    if raw is None or raw.empty:
        raise RuntimeError("no rows from yfinance (check network or symbol)")
    df = raw.dropna(how="any")
    cols = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise KeyError(f"missing columns: {missing}")
    return df[cols].copy()


def load_ohlcv():
    """入口：优先读 ETH_BASELINE_DATA 指向的 CSV，否则走 Yahoo。"""
    p = os.environ.get("ETH_BASELINE_DATA")
    if p:
        return _load_ohlcv_csv(p)
    return fetch_ohlcv_from_web()


def plot_candles_only(df, path_png=OUT_PNG):
    """只画 K 线；统计/蒙特卡洛等一律未实现。"""
    import mplfinance as mpf

    mpf.plot(
        df,
        type="candle",
        style=STYLE_OVERRIDE,
        title="ETH-USD daily (baseline)",
        ylabel="Price",
        volume=True,
        tight_layout=True,
        savefig=dict(fname=path_png, dpi=120, bbox_inches="tight"),
    )


def main():
    # 整条流水线堆在 main；无分层、无配置对象
    data = load_ohlcv()
    # YEARS_WANTED 尚未用于自检窗口长度（技术债）
    plot_candles_only(data)
    print(f"wrote {OUT_PNG} rows={len(data)}")


if __name__ == "__main__":
    main()
