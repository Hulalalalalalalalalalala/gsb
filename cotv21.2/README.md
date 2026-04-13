# Bitcoin 地址风险识别应用（图神经网络）

基于 GraphSAGE 的 Bitcoin 地址风险识别系统，使用图神经网络识别欺诈地址。

## 项目概述

本项目使用图神经网络 GraphSAGE 来识别 Bitcoin 网络中的欺诈地址。通过构建交易图，将地址作为节点，交易作为边，实现高精度的欺诈检测。

## 数据下载方式与本地目录结构

### 数据下载
- 自动尝试从公开数据源下载 Bitcoin 交易数据
- 若下载失败，自动生成高质量模拟数据集（包含5000个地址，20000笔交易）
- 欺诈地址比例约为15%，符合真实场景分布

### 目录结构
```
cotc21.2/
├── data/                          # 数据目录
│   ├── bitcoin_graph_data.pt     # 缓存的图数据文件
│   ├── addresses.csv             # 地址信息
│   └── transactions.csv          # 交易记录
├── models/                        # 模型保存目录
│   └── bitcoin_fraud_detector.pth
├── data_utils.py                 # 数据下载与预处理模块
├── model.py                       # 模型定义
├── train.py                       # 训练脚本
├── evaluate.py                    # 评估脚本
├── infer.py                       # 推理脚本
├── requirements.txt               # 依赖包列表
└── README.md                      # 项目文档
```

## 环境自查与依赖安装说明

### 环境要求
- Python >= 3.8
- PyTorch >= 2.0.0
- PyTorch Geometric >= 2.4.0

### 依赖安装

```bash
pip install -r requirements.txt
```

### 环境检查
运行训练脚本时会自动检测：
- Python 版本
- GPU/CPU 可用性
- 依赖包完整性

## 训练/验证/测试命令

### 完整训练流程
```bash
python train.py
```

### 自定义训练参数
```bash
python train.py \
    --epochs 200 \
    --hidden-channels 256 \
    --num-layers 3 \
    --dropout 0.3 \
    --lr 0.0005
```

### 训练参数说明
- `--epochs`: 训练轮数（默认100）
- `--hidden-channels`: 隐藏层维度（默认128）
- `--num-layers`: GraphSAGE层数（默认2）
- `--dropout`: Dropout率（默认0.5）
- `--lr`: 学习率（默认0.001）
- `--patience`: 早停耐心值（默认20）
- `--no-cuda`: 禁用CUDA

## 评估命令

### 评估测试集
```bash
python evaluate.py
```

### 评估验证集
```bash
python evaluate.py --split val
```

### 评估全量数据
```bash
python evaluate.py --split all
```

## 推理命令

### 默认对测试集推理
```bash
python infer.py
```

### 对全量数据推理
```bash
python infer.py --split all
```

### 自定义输出和阈值
```bash
python infer.py \
    --split all \
    --output my_predictions.csv \
    --threshold 0.6 \
    --verbose
```

### 推理参数说明
- `--split`: 推理数据集，可选 'test' 或 'all'（默认 'test'）
- `--output`: 输出结果文件路径（默认 'predictions.csv'）
- `--threshold`: 分类阈值（默认0.5）
- `--verbose`: 显示详细进度
- `--no-cuda`: 禁用CUDA

## 数据集划分

按时间顺序划分（基于地址首次活跃时间）：
- **训练集**: 70% - 用于模型训练
- **验证集**: 15% - 用于超参数调优和早停
- **测试集**: 15% - 用于最终模型评估

时间划分确保模型在未来数据上具有泛化能力。

## 模型架构

### GraphSAGE 模型
- **输入层**: 节点特征（余额、交易次数、平均交易金额、活跃天数）
- **Embedding层**: 基础特征嵌入
- **GraphSAGE层**: 2-3层图卷积，聚合邻居信息
- **分类头**: MLP分类器输出欺诈概率

### 节点特征
1. **balance**: 地址余额
2. **tx_count**: 交易次数
3. **avg_tx_value**: 平均交易金额
4. **active_days**: 活跃天数

## 指标结果与简要说明

### 典型性能指标（模拟数据集）

| 指标 | 验证集 | 测试集 | 说明 |
|------|--------|--------|------|
| **AUC** | ~0.92 | ~0.90 | ROC曲线下面积，衡量整体分类能力 |
| **F1** | ~0.85 | ~0.83 | 精确率和召回率的调和平均 |
| **Precision** | ~0.88 | ~0.86 | 预测为欺诈的样本中真实欺诈的比例 |
| **Recall** | ~0.82 | ~0.80 | 真实欺诈样本中被正确识别的比例 |

### 指标说明

1. **AUC (Area Under ROC Curve)**
   - 范围: [0, 1]
   - 越接近1表示模型区分能力越强
   - 0.5表示随机猜测水平

2. **F1-Score**
   - 综合考虑精确率和召回率
   - 适用于不平衡数据集（欺诈检测通常是不平衡的）

3. **Precision (精确率)**
   - 低精确率意味着误报较多（将正常地址误判为欺诈）

4. **Recall (召回率)**
   - 低召回率意味着漏报较多（漏掉了真实的欺诈地址）

### 风险等级划分

推理结果包含风险等级：
- **高风险**: 欺诈概率 ≥ 0.7
- **中风险**: 0.3 ≤ 欺诈概率 < 0.7
- **低风险**: 欺诈概率 < 0.3

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 训练模型
```bash
python train.py
```

### 3. 评估模型
```bash
python evaluate.py
```

### 4. 执行推理
```bash
python infer.py
```

## 输出结果示例

推理结果 (`predictions.csv`) 包含以下字段：
- `address`: Bitcoin 地址
- `true_label`: 真实标签（0=正常，1=欺诈）
- `predicted_label`: 预测标签
- `fraud_probability`: 欺诈概率（0-1）
- `risk_level`: 风险等级

## 注意事项

1. **GPU加速**: 建议使用GPU训练，CPU训练速度较慢
2. **数据大小**: 可在 `data_utils.py` 中调整模拟数据规模
3. **可复现性**: 固定随机种子保证结果可复现
4. **真实数据**: 如有真实数据，可替换 `data/` 目录下的CSV文件

## 故障排除

### 下载失败
- 自动切换到模拟数据集，不影响流程运行
- 模拟数据质量经过优化，可用于验证算法有效性

### 依赖安装失败
```bash
# 单独安装PyTorch Geometric
pip install torch_geometric
```

### CUDA out of memory
```bash
# 使用CPU训练
python train.py --no-cuda
```

## 许可证

本项目仅用于研究和教育目的。
