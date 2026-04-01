import pandas as pd
import numpy as np
from scipy import stats


def calculate_summary_stats(returns: pd.Series) -> dict:
    n = len(returns)
    mean = returns.mean()
    var = returns.var(ddof=1)
    skew = stats.skew(returns)
    kurt = stats.kurtosis(returns, fisher=True)
    
    jb_stat, jb_pvalue = stats.jarque_bera(returns)
    
    return {
        "样本量": n,
        "均值": mean,
        "方差": var,
        "偏度": skew,
        "峰度(超额)": kurt,
        "JB统计量": jb_stat,
        "JB p值": jb_pvalue
    }


def rolling_skew_kurtosis(returns: pd.Series, window: int) -> pd.DataFrame:
    return pd.DataFrame({
        "滚动偏度": returns.rolling(window=window).apply(lambda x: stats.skew(x)),
        "滚动峰度": returns.rolling(window=window).apply(lambda x: stats.kurtosis(x, fisher=True))
    }, index=returns.index)


def qq_plot_data(returns: pd.Series) -> tuple:
    (theo_q, sample_q), _ = stats.probplot(returns, dist="norm")
    return theo_q, sample_q


def normal_pdf_range(returns: pd.Series, num_points: int = 100) -> tuple:
    mu = returns.mean()
    sigma = returns.std()
    x = np.linspace(returns.min(), returns.max(), num_points)
    y = stats.norm.pdf(x, mu, sigma)
    return x, y
