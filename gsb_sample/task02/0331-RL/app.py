import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_loader import load_eth_data, filter_date_range, calculate_returns, winsorize
from indicators import rolling_volatility, bollinger_bands
from statistics import calculate_summary_stats, rolling_skew_kurtosis, qq_plot_data, normal_pdf_range
from simulation import estimate_gbm_parameters, simulate_gbm, calculate_quantiles
from var import historical_var, calculate_var_violations


st.set_page_config(page_title="ETH 风险分析 Dashboard", layout="wide")


@st.cache_data
def get_cached_data():
    return load_eth_data()


@st.cache_data
def get_filtered_data(_df, start_date, end_date):
    return filter_date_range(_df, start_date, end_date)


@st.cache_data
def get_returns(prices, method, winsorize_pct):
    rets = calculate_returns(prices, method)
    if winsorize_pct > 0:
        rets = winsorize(rets, winsorize_pct)
    return rets


def main():
    st.title("ETH 风险分析 Dashboard")
    
    df, message = get_cached_data()
    
    if df is None:
        st.error(message)
        return
    
    st.success(message)
    
    with st.sidebar:
        st.header("参数设置")
        
        st.subheader("数据与日期")
        min_date = df.index.min().date()
        max_date = df.index.max().date()
        start_date = st.date_input("起始日期", value=min_date, min_value=min_date, max_value=max_date)
        end_date = st.date_input("结束日期", value=max_date, min_value=min_date, max_value=max_date)
        
        st.subheader("收益设置")
        return_method = st.selectbox("收益算法", ["simple", "log"], format_func=lambda x: "简单收益" if x == "simple" else "对数收益")
        winsorize_pct = st.slider("Winsorize 截尾比例", 0.0, 0.05, 0.0, 0.005)
        annualization_factor = st.selectbox("年化天数", [252, 365])
        
        st.subheader("技术指标")
        window_size = st.slider("滚动窗口长度", 5, 120, 20)
        
        st.subheader("蒙特卡洛模拟")
        use_recent_252 = st.checkbox("仅用最近 252 根K估计参数", value=True)
        horizon = st.selectbox("预测 Horizon", [1, 5], format_func=lambda x: f"{x} 个交易日")
        n_paths = st.slider("模拟路径数", 100, 5000, 1000, 100)
        seed = st.slider("随机种子", 1, 9999, 42)
        
        st.subheader("历史 VaR")
        var_window = st.slider("VaR 滚动窗口", 50, 500, 252)
    
    df_filtered = get_filtered_data(df, pd.Timestamp(start_date), pd.Timestamp(end_date))
    
    prices = df_filtered["Close"]
    returns = get_returns(prices, return_method, winsorize_pct)
    
    st.header("一、数据与行情")
    
    bb = bollinger_bands(prices, window_size)
    vol = rolling_volatility(prices, window_size, annualization_factor)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        row_heights=[0.7, 0.3], vertical_spacing=0.05)
    
    fig.add_trace(go.Candlestick(
        x=df_filtered.index,
        open=df_filtered["Open"],
        high=df_filtered["High"],
        low=df_filtered["Low"],
        close=df_filtered["Close"],
        name="K线"
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=bb.index, y=bb["BB_Upper"], name="布林带上轨", 
                             line=dict(color="rgba(255, 100, 100, 0.7)", dash="dash")), row=1, col=1)
    fig.add_trace(go.Scatter(x=bb.index, y=bb["BB_Mid"], name="布林带中轨", 
                             line=dict(color="rgba(100, 150, 255, 0.7)")), row=1, col=1)
    fig.add_trace(go.Scatter(x=bb.index, y=bb["BB_Lower"], name="布林带下轨", 
                             line=dict(color="rgba(100, 255, 100, 0.7)", dash="dash")), row=1, col=1)
    
    fig.add_trace(go.Bar(x=df_filtered.index, y=df_filtered["Volume"], name="成交量",
                         marker_color="rgba(100, 100, 200, 0.5)"), row=2, col=1)
    
    fig.update_layout(height=600, title="ETH-USD K线 + 布林带 + 成交量", xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    fig_vol = go.Figure()
    fig_vol.add_trace(go.Scatter(x=vol.index, y=vol, name="滚动年化波动率",
                                 line=dict(color="darkorange")))
    fig_vol.update_layout(height=300, title=f"滚动波动率 (窗口={window_size}, 年化天数={annualization_factor})")
    st.plotly_chart(fig_vol, use_container_width=True)
    
    st.header("二、收益分布")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(x=returns, name="实际收益", histnorm="probability density",
                                        opacity=0.7, nbinsx=50))
        
        x_norm, y_norm = normal_pdf_range(returns)
        fig_hist.add_trace(go.Scatter(x=x_norm, y=y_norm, name="同均值同方差正态分布",
                                      line=dict(color="red", width=2)))
        fig_hist.update_layout(title="收益直方图 vs 正态对照", height=400)
        st.plotly_chart(fig_hist, use_container_width=True)
        
        theo_q, sample_q = qq_plot_data(returns)
        fig_qq = go.Figure()
        fig_qq.add_trace(go.Scatter(x=theo_q, y=sample_q, mode="markers", name="样本分位数",
                                    opacity=0.6))
        min_q = min(min(theo_q), min(sample_q))
        max_q = max(max(theo_q), max(sample_q))
        fig_qq.add_trace(go.Scatter(x=[min_q, max_q], y=[min_q, max_q], mode="lines",
                                    name="参考线(45度)", line=dict(color="red", dash="dash")))
        fig_qq.update_layout(title="Q-Q 图", xaxis_title="理论分位数", yaxis_title="样本分位数", height=400)
        st.plotly_chart(fig_qq, use_container_width=True)
    
    with col2:
        stats_dict = calculate_summary_stats(returns)
        st.subheader("统计摘要")
        for k, v in stats_dict.items():
            if k in ["样本量", "违规笔数"]:
                st.metric(k, f"{int(v)}")
            elif k in ["JB p值"]:
                st.metric(k, f"{v:.4f}")
            else:
                st.metric(k, f"{v:.6f}")
        
        st.markdown("---")
        p_val = stats_dict["JB p值"]
        if p_val < 0.05:
            st.error("✅ Jarque-Bera 检验: 显著拒绝正态分布假设")
        else:
            st.success("✅ Jarque-Bera 检验: 不能拒绝正态分布假设")
    
    st.header("三、蒙特卡洛 GBM 模拟")
    
    if use_recent_252 and len(df) >= 252:
        sim_prices = df["Close"].iloc[-252:]
    else:
        sim_prices = prices
    
    sim_returns = calculate_returns(sim_prices, return_method)
    params = estimate_gbm_parameters(sim_returns, annualization_factor)
    S0 = prices.iloc[-1]
    
    st.write(f"**参数估计** (基于{'最近252根K' if use_recent_252 else '选定区间'})")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("当日漂移 μ", f"{params['daily_mu']:.6f}")
    col_b.metric("当日波动 σ", f"{params['daily_sigma']:.6f}")
    col_c.metric("年化漂移", f"{params['annual_mu']:.4f}")
    col_d.metric("年化波动", f"{params['annual_sigma']:.4f}")
    
    st.caption("说明: 年化漂移 = 日漂移 × 年化天数；年化波动 = 日波动 × √年化天数")
    
    paths, step_indices = simulate_gbm(
        S0, params["daily_mu"], params["daily_sigma"],
        days=horizon, steps_per_day=24, n_paths=n_paths, seed=seed
    )
    
    fig_paths = go.Figure()
    for i in range(min(100, n_paths)):
        fig_paths.add_trace(go.Scatter(x=step_indices, y=paths[i], 
                                       line=dict(width=0.8),
                                       opacity=0.4,
                                       showlegend=False))
    
    fig_paths.add_trace(go.Scatter(x=step_indices, y=np.mean(paths, axis=0),
                                   name="平均路径", line=dict(color="red", width=2)))
    fig_paths.update_layout(
        title=f"GBM 模拟路径 (前100条, 每日24子步, 共 {horizon} 个交易日)",
        xaxis_title="子步索引",
        yaxis_title="价格",
        height=450
    )
    st.plotly_chart(fig_paths, use_container_width=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        final_prices = paths[:, -1]
        fig_final = go.Figure()
        fig_final.add_trace(go.Histogram(x=final_prices, name="终点价格", nbinsx=50, opacity=0.7))
        fig_final.add_vline(x=S0, line_dash="dash", line_color="red", 
                            annotation_text="起始价格")
        fig_final.update_layout(title="终点价格分布", height=350)
        st.plotly_chart(fig_final, use_container_width=True)
    
    with col2:
        st.subheader("终点价格分位数")
        quantiles_df = calculate_quantiles(paths)
        st.dataframe(quantiles_df, hide_index=True, use_container_width=True)
    
    st.header("四、历史 VaR")
    
    var_series = historical_var(returns, var_window, 0.95)
    var_result = calculate_var_violations(returns, var_series)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("有效样本长度", var_result["有效样本长度"])
    col2.metric("违规笔数", var_result["违规笔数"])
    col3.metric("违规率", f"{var_result['违规率']:.2%}")
    
    st.markdown("---")
    expected_rate = 0.05
    actual_rate = var_result["违规率"]
    diff = actual_rate - expected_rate
    
    if abs(diff) < 0.01:
        st.success(f"实际违规率 {actual_rate:.2%} 与理论 5% 非常接近，VaR 校准良好。")
    elif diff > 0:
        st.warning(f"实际违规率 {actual_rate:.2%} 高于理论 5%，说明该 VaR 偏乐观，低估了尾部风险。")
    else:
        st.info(f"实际违规率 {actual_rate:.2%} 低于理论 5%，说明该 VaR 偏保守。")
    
    fig_var = go.Figure()
    fig_var.add_trace(go.Scatter(x=returns.index, y=returns, name="次日实际收益",
                                 mode="markers", marker=dict(size=4, opacity=0.6)))
    fig_var.add_trace(go.Scatter(x=var_series.index, y=var_series, name="95% 历史 VaR",
                                 line=dict(color="red", width=2)))
    
    violations = var_result["违规标记"]
    violation_dates = returns.index[:-1][violations]
    violation_values = returns.shift(-1)[violations]
    
    fig_var.add_trace(go.Scatter(x=violation_dates, y=violation_values,
                                 mode="markers", name="跌破 VaR",
                                 marker=dict(size=8, color="red", symbol="x")))
    
    fig_var.update_layout(title="历史 VaR (滚动窗口) 与实际次日收益对比", height=450)
    st.plotly_chart(fig_var, use_container_width=True)


if __name__ == "__main__":
    main()
