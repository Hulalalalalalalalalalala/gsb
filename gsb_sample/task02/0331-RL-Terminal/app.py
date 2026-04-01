import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from data_loader import load_ohlcv, filter_by_date
from returns import calculate_returns, winsorize, calculate_statistics
from indicators import rolling_volatility, bollinger_bands
from monte_carlo import estimate_gbm_parameters, simulate_gbm_multi_day, get_endpoint_quantiles
from var import historical_var, count_var_violations

st.set_page_config(page_title="ETH Quant Analytics", layout="wide")

st.title("ETH-USD 量化分析工作台")

with st.sidebar:
    st.header("⚙️ 配置面板")
    
    st.subheader("📊 数据源")
    use_local_csv = st.checkbox("使用本地 CSV (环境变量: ETH_BASELINE_DATA)", value=True)
    
    st.subheader("📅 日期区间")
    df_full = load_ohlcv(use_local_csv)
    min_date = df_full.index.date.min()
    max_date = df_full.index.date.max()
    start_date = st.date_input("起始日期", min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("结束日期", max_date, min_value=min_date, max_value=max_date)
    
    st.subheader("📈 收益计算")
    return_method = st.radio("收益算法", ["log", "simple"], 
                             format_func=lambda x: "对数收益" if x == "log" else "简单收益")
    
    use_winsorize = st.checkbox("启用 Winsorize 截尾")
    if use_winsorize:
        winsor_pct = st.slider("截尾比例 (上下各%)", 0.1, 5.0, 1.0, 0.1) / 100.0
    
    annualize_days = st.selectbox("年化天数", [252, 365], index=0)
    
    st.subheader("📊 滚动指标")
    indicator_type = st.radio("滚动指标", ["波动率", "布林带", "全部"])
    rolling_window = st.slider("滚动窗口", 5, 120, 20, 5)
    
    st.subheader("🎲 蒙特卡洛模拟")
    use_recent_252 = st.checkbox("仅用最近 252 根 K 估计参数")
    horizon_days = st.select_slider("展望交易日", options=[1, 5])
    n_paths = st.slider("模拟路径数", 100, 5000, 1000, 100)
    mc_seed = st.number_input("随机种子", 1, 99999, 42)
    
    st.subheader("📉 历史 VaR")
    var_window = st.slider("VaR 滚动窗口", 100, 500, 252, 10)
    var_confidence = st.selectbox("置信水平", [0.95, 0.99], index=0)

df = filter_by_date(df_full, start_date, end_date)
closes = df["Close"]

raw_returns = calculate_returns(closes, return_method)
if use_winsorize:
    returns_series = winsorize(raw_returns, winsor_pct, winsor_pct)
else:
    returns_series = raw_returns

st.header("一、K 线与滚动指标")

fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                    row_heights=[0.7, 0.3], vertical_spacing=0.05)

fig.add_trace(go.Candlestick(
    x=df.index, open=df["Open"], high=df["High"], low=df["Low"], close=df["Close"],
    name="K线"), row=1, col=1)

if indicator_type in ["波动率", "全部"]:
    vol = rolling_volatility(closes, rolling_window, annualize_days)
    fig.add_trace(go.Scatter(
        x=vol.index, y=vol, name=f"滚动波动率 ({rolling_window}d)",
        line=dict(color="orange", width=1.5)), row=1, col=1)

if indicator_type in ["布林带", "全部"]:
    bb = bollinger_bands(closes, rolling_window)
    fig.add_trace(go.Scatter(
        x=bb.index, y=bb["BB_Upper"], name="BB上轨",
        line=dict(color="rgba(0,100,255,0.7)", width=1, dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=bb.index, y=bb["BB_Middle"], name="BB中轨",
        line=dict(color="rgba(0,100,255,0.7)", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=bb.index, y=bb["BB_Lower"], name="BB下轨",
        line=dict(color="rgba(0,100,255,0.7)", width=1, dash="dash")), row=1, col=1)

fig.add_trace(go.Bar(
    x=df.index, y=df["Volume"], name="成交量",
    marker_color="rgba(100,100,100,0.5)"), row=2, col=1)

fig.update_layout(height=600, xaxis_rangeslider_visible=False)
fig.update_yaxes(title_text="价格", row=1, col=1)
fig.update_yaxes(title_text="成交量", row=2, col=1)
st.plotly_chart(fig, use_container_width=True)

st.header("二、收益分布分析")
col1, col2 = st.columns([1.5, 1])

with col1:
    clean_rets = returns_series.dropna()
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=clean_rets, nbinsx=50, name="实际收益",
        histnorm="probability density"))
    
    mu, std = stats.norm.fit(clean_rets)
    x = np.linspace(clean_rets.min(), clean_rets.max(), 100)
    pdf = stats.norm.pdf(x, mu, std)
    
    fig.add_trace(go.Scatter(
        x=x, y=pdf, name=f"N({mu:.4f}, {std:.4f}²)",
        line=dict(color="red", width=2)))
    
    fig.update_layout(
        title="收益直方图 vs 正态分布",
        xaxis_title="日收益",
        yaxis_title="密度",
        height=350,
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    qq_theory = stats.probplot(clean_rets, dist="norm")
    fig_qq = go.Figure()
    fig_qq.add_trace(go.Scatter(
        x=qq_theory[0][0], y=qq_theory[0][1], mode="markers",
        name="Q-Q 点", opacity=0.6))
    fig_qq.add_trace(go.Scatter(
        x=qq_theory[0][0], y=qq_theory[1][1] * qq_theory[0][0] + qq_theory[1][0],
        mode="lines", name="参考线", line=dict(color="red", dash="dash")))
    fig_qq.update_layout(
        title="Q-Q 图 (偏离对角线 = 偏离正态)",
        height=350, xaxis_title="理论分位数", yaxis_title="样本分位数")
    st.plotly_chart(fig_qq, use_container_width=True)

with col2:
    stats_dict = calculate_statistics(clean_rets)
    
    st.subheader("📊 统计摘要")
    df_stats = pd.DataFrame({
        "指标": ["样本量", "均值", "方差", "偏度", "超额峰度", "JB 统计量", "JB p值"],
        "数值": [
            f"{stats_dict['n_samples']:.0f}",
            f"{stats_dict['mean']:.6f}",
            f"{stats_dict['variance']:.6f}",
            f"{stats_dict['skewness']:.4f}",
            f"{stats_dict['kurtosis']:.4f}",
            f"{stats_dict['jb_stat']:.2f}",
            f"{stats_dict['jb_pvalue']:.4g}"
        ]
    })
    st.dataframe(df_stats, hide_index=True, use_container_width=True)
    
    st.markdown("---")
    st.subheader("✅ 正态性检验")
    st.info(f"""
    **Jarque-Bera 检验**
    
    p值 = {stats_dict['jb_pvalue']:.4g}
    
    选用理由: JB检验专门针对大样本金融数据设计，直接检验偏度和峰度是否符合正态，是量化研究中的标准做法。
    
    {"❌ 强烈拒绝正态假设 (p < 0.05)" if stats_dict['jb_pvalue'] < 0.05 
     else "⚠️ 不能拒绝正态假设"}
    """)

st.header("三、蒙特卡洛 GBM 模拟")

gbm_params = estimate_gbm_parameters(
    closes, annualize_days, 252 if use_recent_252 else None)

S0 = closes.iloc[-1]
paths = simulate_gbm_multi_day(
    S0, gbm_params["mu_daily"], gbm_params["sigma_daily"],
    days=horizon_days, steps_per_day=24, n_paths=n_paths, seed=mc_seed)

quantiles, endpoints, endpoint_returns = get_endpoint_quantiles(paths)

col1, col2 = st.columns([1.5, 1])

with col1:
    fig_paths = go.Figure()
    for i in range(min(100, n_paths)):
        fig_paths.add_trace(go.Scatter(
            y=paths[:, i], mode="lines", opacity=0.5,
            line=dict(width=0.8),
            showlegend=False))
    
    fig_paths.add_trace(go.Scatter(
        y=np.percentile(paths, 50, axis=1),
        mode="lines", line=dict(color="red", width=2),
        name="中位数路径"))
    
    fig_paths.update_layout(
        title=f"GBM 路径图 (前100条) - {horizon_days}交易日, 每日24子步",
        xaxis_title="子步索引 (0-" + str(horizon_days * 24) + ")",
        yaxis_title="价格",
        height=400
    )
    st.plotly_chart(fig_paths, use_container_width=True)
    
    fig_end = go.Figure()
    fig_end.add_trace(go.Histogram(x=endpoint_returns, nbinsx=50))
    fig_end.update_layout(
        title=f"终点收益分布 ({horizon_days}交易日)",
        xaxis_title="总收益", height=300)
    st.plotly_chart(fig_end, use_container_width=True)

with col2:
    st.subheader("📐 参数估计")
    st.info(f"""
    估计窗口: {"最近252根K" if use_recent_252 else "全样本"}
    
    日漂移 μ_daily = {gbm_params['mu_daily']:.6f}
    日波动 σ_daily = {gbm_params['sigma_daily']:.6f}
    
    年化漂移 μ × {annualize_days} = {gbm_params['mu_annual']:.4%}
    年化波动 σ × √{annualize_days} = {gbm_params['sigma_annual']:.4%}
    """)
    
    st.subheader("📊 终点价格分位数")
    q_df = pd.DataFrame([
        {"分位数": f"{int(q*100)}%", "价格": f"{v['price']:.2f}", "收益": f"{v['return']:.2%}"}
        for q, v in quantiles.items()
    ])
    st.dataframe(q_df, hide_index=True, use_container_width=True)
    
    st.caption(f"起始价格 S0 = {S0:.2f} USD")

st.header("四、历史 VaR 回测")

var_series = historical_var(raw_returns, var_window, var_confidence)
vr = count_var_violations(raw_returns, var_series)

fig_var = go.Figure()
fig_var.add_trace(go.Scatter(
    x=vr["next_day_returns"].index, y=vr["next_day_returns"],
    mode="markers", name="次日真实收益", opacity=0.7))
fig_var.add_trace(go.Scatter(
    x=vr["var_series"].index, y=vr["var_series"],
    mode="lines", name=f"历史 VaR ({int(var_confidence*100)}%)",
    line=dict(color="red")))

violation_dates = vr["next_day_returns"][vr["violation_mask"]].index
violation_rets = vr["next_day_returns"][vr["violation_mask"]].values
fig_var.add_trace(go.Scatter(
    x=violation_dates, y=violation_rets,
    mode="markers", marker=dict(color="red", size=10, symbol="x"),
    name=f"跌破 VaR ({vr['n_violations']}次)"))

fig_var.update_layout(
    title="历史 VaR 与次日收益对照",
    yaxis_title="收益", height=400)
st.plotly_chart(fig_var, use_container_width=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("有效样本数", vr['n_valid'])
with col2:
    st.metric("违规笔数", vr['n_violations'])
with col3:
    st.metric("违规率", f"{vr['violation_rate']:.2%}")

st.info(f"""
**⚠️ VaR 违规率分析**

名义违规率应为 {(1-var_confidence):.0%}，实际违规率为 {vr['violation_rate']:.2%}。

差值: {abs(vr['violation_rate'] - (1-var_confidence)):.2%}
""")

st.caption("说明：这是历史模拟法 VaR，滚动窗口内分位数预测下一日收益，与蒙特卡洛模拟为独立模块。")

st.markdown("---")
st.success("✅ 所有分析模块已加载完成")
