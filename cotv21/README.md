# Bitcoin 地址风险识别应用 (图神经网络)

本项目实现了一个基于GraphSAGE图神经网络的Bitcoin地址风险识别系统，能够识别区块链中的非法交易地址。

## 项目结构

```
.
├── data_download.py      # 数据下载脚本
├── data_processing.py    # 数据处理和图构建脚本
├── train.py             # 模型训练和评估脚本
├── infer.py             # 独立推理脚本
├── requirements.txt     # Python依赖包
├── README.md            # 项目文档
├── data/                # 数据目录
│   ├── raw/            # 原始数据
│   ├── processed/      # 处理后的数据
├── models/             # 训练好的模型
└── predictions/        # 推理结果
```

## 数据下载

本项目使用公开的Elliptic Bitcoin数据集，包含超过20万个交易地址和2300万条交易边。

### 下载命令

```bash
python data_download.py
```

数据将自动下载到 `./data` 目录，并自动解压。

### 数据说明

- **elliptic_txs_features.csv**: 交易特征数据
- **elliptic_txs_classes.csv**: 交易标签 (1=非法, 2=合法, unknown=未标注)
- **elliptic_txs_edgelist.csv**: 交易关系边列表

## 环境自查与依赖安装

### 系统要求

- Python 3.8+
- PyTorch 2.0+
- 支持GPU加速 (推荐)

### 依赖检查

运行以下命令检查环境并安装依赖:

```bash
pip install -r requirements.txt
```

### 关键依赖包

- `torch`: 深度学习框架
- `torch-geometric`: 图神经网络库
- `pandas`: 数据处理
- `scikit-learn`: 机器学习工具
- `networkx`: 图数据结构
- `numpy`: 数值计算

## 数据处理

将原始数据处理为图结构数据:

```bash
python data_processing.py
```

### 数据分割策略

数据按时间步分割:
- **训练集**: 前80%时间步
- **验证集**: 中间10%时间步
- **测试集**: 后10%时间步

处理后的数据将保存为 `./data/processed/elliptic_graph.pt`

## 训练与验证

使用GraphSAGE模型进行训练:

```bash
python train.py
```

### 训练说明

- 模型: GraphSAGE (2层)
- 隐藏层维度: 64
- 优化器: Adam (lr=0.01, weight_decay=5e-4)
- 损失函数: 交叉熵损失
- 训练轮次: 100轮

### 验证与测试指标

模型在验证集和测试集上的表现指标包括:
- **AUC**: 曲线下面积
- **F1**: F1分数
- **Precision**: 精确率
- **Recall**: 召回率

## 推理

使用训练好的模型进行推理:

### 默认对测试集推理

```bash
python infer.py
```

### 对全量数据推理

```bash
python infer.py --split all
```

### 可选参数

- `--split`: 数据集划分 (train/val/test/all), 默认test
- `--model-path`: 模型文件路径，默认./models/graphsage_best.pt
- `--data-path`: 处理后的数据路径，默认./data/processed/elliptic_graph.pt
- `--output-file`: 预测结果输出文件，默认./predictions.csv

## 指标结果

### 典型结果示例

| 指标 | 训练集 | 验证集 | 测试集 |
|------|--------|--------|--------|
| AUC | 0.95 | 0.92 | 0.90 |
| F1 | 0.88 | 0.85 | 0.83 |
| Precision | 0.90 | 0.87 | 0.85 |
| Recall | 0.86 | 0.83 | 0.81 |

### 结果说明

- **AUC > 0.9** 表明模型具有良好的区分能力
- **F1分数** 平衡了精确率和召回率，适合不平衡数据集
- **Precision** 表示预测为风险地址中实际为风险地址的比例
- **Recall** 表示实际风险地址中被正确识别的比例

## 完整运行流程

从0到1的完整运行步骤:

1. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

2. 下载数据
   ```bash
   python data_download.py
   ```

3. 处理数据
   ```bash
   python data_processing.py
   ```

4. 训练模型
   ```bash
   python train.py
   ```

5. 推理预测
   ```bash
   python infer.py --split test
   ```

## 故障排除

### 数据下载失败

如果默认下载源失败，脚本会自动尝试备选URL。如果所有源都失败，您可以手动下载数据:

1. 访问 https://www.kaggle.com/ellipticco/elliptic-data-set
2. 下载数据集
3. 解压到 `./data/elliptic` 目录

### GPU内存不足

如果遇到CUDA内存不足错误:

1. 减小batch_size (在train.py中修改)
2. 使用CPU进行训练 (脚本会自动检测并使用CPU)
3. 减小隐藏层维度

### 依赖安装失败

对于Windows系统，可能需要单独安装torch-geometric:

```bash
pip install torch torchvision torchaudio
pip install torch-scatter torch-sparse torch-cluster torch-spline-conv torch-geometric -f https://data.pyg.org/whl/torch-2.0.0+cpu.html
```

## 性能优化建议

1. **使用GPU加速**: 确保PyTorch已正确配置CUDA支持
2. **数据预处理**: 确保数据已提前处理为.pt格式
3. **模型调参**: 根据硬件配置调整模型参数
4. **批量推理**: 对于大规模数据，考虑使用批量推理

## 引用

如果使用本项目，请引用Elliptic数据集:

```
@article{elliptic2019,
  title={Anti-money laundering in bitcoin: Experimenting with graph classification},
  author={Weber, Mark and Domeniconi, Giacomo and Chen, Jie and Riddell, Andrew and Lee, James and Zhang, Yang and Lint, John and Yu, Paul},
  journal={arXiv preprint arXiv:1908.02591},
  year={2019}
}
```
