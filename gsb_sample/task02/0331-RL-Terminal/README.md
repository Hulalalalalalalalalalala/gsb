# ETH 量化分析工作台

一个完整的 Streamlit 量化分析应用，包含 K 线行情、收益分布、蒙特卡洛模拟和历史 VaR 回测。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动应用

### 在线模式（从 Yahoo Finance 拉取数据）
```bash
streamlit run app.py
```

### 离线模式（使用本地 CSV 数据）
准备 CSV 文件（必须包含 Date 索引和 Open, High, Low, Close, Volume 列），然后：
```bash
ETH_BASELINE_DATA=/path/to/your/eth_data.csv streamlit run app.py
```

## 主要功能

### 1. 数据与行情
- 支持在线/本地 CSV 数据源切换
- 可自定义日期区间
- K 线图 + 成交量
- 滚动波动率或布林带，窗口长度可调
- 可选 Winsorize 上下截尾去极值

### 2. 收益分布分析
- 收益直方图 + 同均值同方差正态分布对照
- Q-Q 图直观展示非正态性
- 完整统计量：样本量、均值、方差、偏度、峰度
- Jarque-Bera 正态性检验
  > 选用理由：JB 检验专门针对大样本金融数据设计，直接检验偏度和峰度是否符合正态，是量化研究中的标准做法。

### 3. 蒙特卡洛 GBM 模拟
- 支持全样本或最近 252 根 K 估计参数
- 展望 1 个或 5 个交易日
- 每日拆分为 24 个子步模拟
- 路径图 + 终点收益分布 + 分位数表

### 4. 历史 VaR 回测
- 滚动窗口计算 95%/99% 历史分位 VaR
- 与真实次日收益对齐
- 违规笔数、违规率统计和分析

## 运行测试

```bash
pytest tests/test_quant.py -q
```
