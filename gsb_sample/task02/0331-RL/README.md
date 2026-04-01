# ETH 风险分析 Dashboard

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动方式

### 在线模式（使用 Yahoo Finance 数据）
```bash
streamlit run app.py
```

### 离线模式（使用本地 CSV 数据）
```bash
DATA_PATH=./data/eth_data.csv streamlit run app.py
```

## 关于正态性检验

本项目选用 Jarque-Bera 检验，原因：
1. Jarque-Bera 专门检验样本偏度和峰度是否符合正态分布，与金融收益的"肥尾"特性高度相关
2. 对于大样本（>50）表现稳定，适合日线级别的时间序列
3. 计算速度快，适合交互式页面实时更新

## 项目结构
```
├── app.py              # Streamlit 主应用
├── data_loader.py      # 数据加载与预处理
├── indicators.py       # 技术指标计算
├── statistics.py       # 统计分析与正态性检验
├── simulation.py       # 蒙特卡洛 GBM 模拟
├── var.py              # 历史 VaR 计算
├── tests/              # 单元测试
└── data/               # 本地数据目录（可选）
```
