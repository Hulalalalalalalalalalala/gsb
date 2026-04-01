import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from scipy import stats
import warnings
import platform

from src import (
    load_ohlcv,
    calculate_returns,
    winsorize,
    rolling_volatility,
    bollinger_bands,
    distribution_stats,
    rolling_skewness,
    rolling_kurtosis,
    estimate_gbm_params,
    simulate_gbm,
    get_terminal_returns,
    get_terminal_quantiles,
    historical_var,
    calculate_var_violations
)

warnings.filterwarnings("ignore")
st.set_page_config(page_title="ETH Analysis Dashboard", layout="wide")

def configure_matplotlib_chinese():
    from matplotlib.font_manager import FontProperties
    import os
    
    font_paths = [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
    ]
    
    chinese_font = None
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                chinese_font = FontProperties(fname=font_path)
                break
            except:
                continue
    
    system = platform.system()
    if system == "Windows":
        plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei"]
    elif system == "Darwin":
        plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC"]
    else:
        plt.rcParams["font.sans-serif"] = ["WenQuanYi Micro Hei", "Droid Sans Fallback"]
    
    plt.rcParams["axes.unicode_minus"] = False
    return chinese_font

chinese_font = configure_matplotlib_chinese()


@st.cache_data
def get_data():
    try:
        df, source = load_ohlcv()
        return df, source, None
    except Exception as e:
        return None, None, str(e)


st.title("ETH-USD Analysis Dashboard")

df, data_source, load_error = get_data()

if load_error:
    st.error(f"Failed to load data: {load_error}")
    st.info("Please use offline mode by setting ETH_BASELINE_DATA environment variable to fixtures/eth_usd_daily_fixture.csv")
    st.stop()

st.sidebar.header("Data & Parameters")

min_date = df.index.min()
max_date = df.index.max()
start_date = st.sidebar.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)
if start_date > end_date:
    st.sidebar.error("Start date must be before end date")

df_filtered = df.loc[start_date:end_date].copy()

return_method = st.sidebar.radio("Return Calculation", ["simple", "log"], index=0)
annualize_days = st.sidebar.radio("Annualization Days", [252, 365], index=0)

use_winsorize = st.sidebar.checkbox("Apply Winsorization", value=False)
winsorize_lower = st.sidebar.slider("Lower Winsorize", 0.0, 0.1, 0.01, 0.005, disabled=not use_winsorize)
winsorize_upper = st.sidebar.slider("Upper Winsorize", 0.0, 0.1, 0.01, 0.005, disabled=not use_winsorize)

rolling_window = st.sidebar.slider("Rolling Window Length", 5, 100, 20, 5)

st.header("一、数据与行情")

st.subheader(f"Data Source: {data_source}")
st.write(f"Date Range: {start_date.date()} to {end_date.date()}")
st.write(f"Total Data Points: {len(df_filtered)}")

st.subheader("K线图 + 成交量 + 滚动指标")

bb = bollinger_bands(df_filtered["Close"], window=rolling_window)
addplots = [
    mpf.make_addplot(bb["SMA"], color="blue", label=f"SMA {rolling_window}"),
    mpf.make_addplot(bb["Upper"], color="orange", linestyle="--", label="Upper Band"),
    mpf.make_addplot(bb["Lower"], color="orange", linestyle="--", label="Lower Band")
]

fig, axes = mpf.plot(
    df_filtered,
    type="candle",
    style="charles",
    title="ETH-USD Daily with Bollinger Bands",
    ylabel="Price (USD)",
    volume=True,
    addplot=addplots,
    figratio=(16, 8),
    returnfig=True
)
st.pyplot(fig)
plt.close(fig)

st.header("二、分布")

returns = calculate_returns(df_filtered["Close"], method=return_method)
if use_winsorize:
    returns = winsorize(returns, lower=winsorize_lower, upper=winsorize_upper)

dist_stats = distribution_stats(returns)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("收益直方图与正态对照")
    fig, ax = plt.subplots(figsize=(10, 6))
    n, bins, patches = ax.hist(returns, bins=50, density=True, alpha=0.6, label="Returns")
    mu, std = stats.norm.fit(returns)
    x = np.linspace(bins[0], bins[-1], 100)
    p = stats.norm.pdf(x, mu, std)
    ax.plot(x, p, 'k', linewidth=2, label=f"Normal Fit (μ={mu:.4f}, σ={std:.4f})")
    if chinese_font:
        ax.set_xlabel("Returns", fontproperties=chinese_font)
        ax.set_ylabel("Density", fontproperties=chinese_font)
        ax.legend(prop=chinese_font)
    else:
        ax.set_xlabel("Returns")
        ax.set_ylabel("Density")
        ax.legend()
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)

with col2:
    st.subheader("Q-Q图")
    fig, ax = plt.subplots(figsize=(10, 6))
    stats.probplot(returns, dist="norm", plot=ax)
    if chinese_font:
        ax.set_title("Q-Q Plot of Returns vs Normal Distribution", fontproperties=chinese_font)
    else:
        ax.set_title("Q-Q Plot of Returns vs Normal Distribution")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)

st.subheader("分布统计量")
stats_df = pd.DataFrame([{
    "统计量": "样本量",
    "值": dist_stats["sample_size"]
}, {
    "统计量": "均值",
    "值": f"{dist_stats['mean']:.6f}"
}, {
    "统计量": "方差",
    "值": f"{dist_stats['variance']:.6f}"
}, {
    "统计量": "偏度",
    "值": f"{dist_stats['skewness']:.4f}"
}, {
    "统计量": "峰度",
    "值": f"{dist_stats['kurtosis']:.4f}"
}, {
    "统计量": "Jarque-Bera统计量",
    "值": f"{dist_stats['jb_statistic']:.4f}"
}, {
    "统计量": "Jarque-Bera p值",
    "值": f"{dist_stats['jb_pvalue']:.6f}"
}])
st.table(stats_df)

st.info("选择Jarque-Bera检验的原因：它专门用于检验样本是否来自正态分布，通过偏度和峰度两个统计量综合判断，适合大样本场景（我们的日频数据通常有较多样本点）。")

st.header("三、蒙特卡洛")

st.sidebar.subheader("蒙特卡洛参数")
use_last_252 = st.sidebar.checkbox("使用最近252根K线估计参数", value=False)
horizon_days = st.sidebar.radio("展望交易日数", [1, 5], index=0)
num_paths = st.sidebar.slider("路径数", 100, 10000, 1000, 100)
random_seed = st.sidebar.number_input("随机种子", value=42, min_value=0)

if use_last_252 and len(df) >= 252:
    est_df = df.iloc[-252:]
else:
    est_df = df

est_returns = calculate_returns(est_df["Close"], method=return_method)
mu, sigma = estimate_gbm_params(est_returns, annualize_days=annualize_days)

st.write(f"漂移率 (μ): {mu:.4%} (年化)")
st.write(f"波动率 (σ): {sigma:.4%} (年化)")

substeps_per_day = 24
substep_indices, paths = simulate_gbm(
    S0=df_filtered["Close"].iloc[-1],
    mu=mu,
    sigma=sigma,
    horizon_days=horizon_days,
    substeps_per_day=substeps_per_day,
    num_paths=num_paths,
    random_seed=random_seed
)

st.subheader("模拟路径图")
fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(substep_indices, paths, lw=0.5, alpha=0.3)
if chinese_font:
    ax.set_xlabel("子步索引", fontproperties=chinese_font)
    ax.set_ylabel("价格 (USD)", fontproperties=chinese_font)
    ax.set_title(f"GBM模拟路径 ({num_paths}条路径, {horizon_days}个交易日, 每日{substeps_per_day}子步)", fontproperties=chinese_font)
else:
    ax.set_xlabel("子步索引")
    ax.set_ylabel("价格 (USD)")
    ax.set_title(f"GBM模拟路径 ({num_paths}条路径, {horizon_days}个交易日, 每日{substeps_per_day}子步)")
ax.grid(True, alpha=0.3)
st.pyplot(fig)
plt.close(fig)

terminal_returns = get_terminal_returns(paths, method=return_method)
terminal_prices = paths[-1, :]

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("终点收益分布")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(terminal_returns, bins=50, density=True, alpha=0.6)
    if chinese_font:
        ax.set_xlabel(f"{return_method.capitalize()} Returns", fontproperties=chinese_font)
        ax.set_ylabel("Density", fontproperties=chinese_font)
        ax.set_title("Terminal Returns Distribution", fontproperties=chinese_font)
    else:
        ax.set_xlabel(f"{return_method.capitalize()} Returns")
        ax.set_ylabel("Density")
        ax.set_title("Terminal Returns Distribution")
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close(fig)

with col2:
    st.subheader("终点价格分位数表")
    price_quantiles = get_terminal_quantiles(terminal_prices)
    qdf = pd.DataFrame(list(price_quantiles.items()), columns=["分位数", "价格 (USD)"])
    qdf["价格 (USD)"] = qdf["价格 (USD)"].round(2)
    st.table(qdf)

st.header("四、历史VaR")

var_window = st.sidebar.slider("VaR滚动窗口", 50, 500, 252, 10)
var_confidence = 0.95

var_series = historical_var(returns, window=var_window, confidence=var_confidence)
n_valid, n_violations, violation_rate = calculate_var_violations(returns, var_series)

st.subheader("历史VaR (95% 置信度) 与违规分析")

fig, ax = plt.subplots(figsize=(16, 6))
aligned_returns = returns.shift(-1).dropna()
common_idx = aligned_returns.index.intersection(var_series.index)
plot_returns = aligned_returns.loc[common_idx]
plot_var = var_series.loc[common_idx]

ax.plot(plot_returns.index, plot_returns.values, label="次日真实收益", lw=0.8)
ax.plot(plot_var.index, plot_var.values, label=f"{int(var_confidence*100)}% 历史VaR", color="red", lw=1.5)
violations = plot_returns < plot_var
ax.scatter(plot_returns.index[violations], plot_returns.values[violations], color="purple", zorder=5, label="违规点")
if chinese_font:
    ax.set_xlabel("日期", fontproperties=chinese_font)
    ax.set_ylabel("收益", fontproperties=chinese_font)
    ax.set_title("历史VaR与真实收益对比", fontproperties=chinese_font)
    ax.legend(prop=chinese_font)
else:
    ax.set_xlabel("日期")
    ax.set_ylabel("收益")
    ax.set_title("历史VaR与真实收益对比")
    ax.legend()
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45)
st.pyplot(fig)
plt.close(fig)

st.subheader("VaR违规统计")
st.write(f"有效样本长度: {n_valid}")
st.write(f"违规笔数: {n_violations}")
st.write(f"违规率: {violation_rate:.2%}")

expected_violation_rate = 1 - var_confidence
st.write(f"\n**分析**: 名义违规率应为 {expected_violation_rate:.0%}，实际违规率为 {violation_rate:.2%}。")
if violation_rate > expected_violation_rate * 1.5:
    st.write("实际违规率明显高于预期，说明历史VaR可能低估了尾部风险。")
elif violation_rate < expected_violation_rate * 0.5:
    st.write("实际违规率明显低于预期，说明历史VaR可能过于保守。")
else:
    st.write("实际违规率与预期较为接近。")
