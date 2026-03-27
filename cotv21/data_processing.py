import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import torch
from torch_geometric.data import Data
import networkx as nx

def load_elliptic_data(data_dir="./data/elliptic"):
    """加载Elliptic数据集"""
    # 加载交易特征
    txs_features = pd.read_csv(os.path.join(data_dir, "elliptic_txs_features.csv"), header=None)
    txs_classes = pd.read_csv(os.path.join(data_dir, "elliptic_txs_classes.csv"))
    txs_edgelist = pd.read_csv(os.path.join(data_dir, "elliptic_txs_edgelist.csv"))
    
    return txs_features, txs_classes, txs_edgelist

def process_data(txs_features, txs_classes, txs_edgelist):
    """处理数据并构建图结构"""
    print("处理数据中...")
    
    # 特征处理
    txs_features.columns = ['txId', 'time_step'] + [f'local_feature_{i}' for i in range(93)] + [f'agg_feature_{i}' for i in range(72)]
    
    # 标签处理
    txs_classes['class'] = txs_classes['class'].map({'1': 1, '2': 0, 'unknown': 2})
    merged_data = txs_features.merge(txs_classes, on='txId', how='left')
    
    # 按时间步分割数据
    time_steps = sorted(merged_data['time_step'].unique())
    total_steps = len(time_steps)
    
    # 80%训练，10%验证，10%测试
    train_steps = time_steps[:int(total_steps * 0.8)]
    val_steps = time_steps[int(total_steps * 0.8):int(total_steps * 0.9)]
    test_steps = time_steps[int(total_steps * 0.9):]
    
    print(f"时间步分布: 训练={len(train_steps)}, 验证={len(val_steps)}, 测试={len(test_steps)}")
    
    # 特征归一化
    feature_cols = [col for col in merged_data.columns if 'feature' in col]
    scaler = StandardScaler()
    merged_data[feature_cols] = scaler.fit_transform(merged_data[feature_cols])
    
    # 构建图
    node_features = merged_data[feature_cols].values
    labels = merged_data['class'].values
    
    # 创建节点ID到索引的映射
    txid_to_idx = {txid: idx for idx, txid in enumerate(merged_data['txId'])}
    
    # 构建边索引
    edges = txs_edgelist[['txId1', 'txId2']].values
    edge_index = []
    for tx1, tx2 in edges:
        if tx1 in txid_to_idx and tx2 in txid_to_idx:
            edge_index.append([txid_to_idx[tx1], txid_to_idx[tx2]])
    
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    
    # 创建掩码
    train_mask = torch.tensor(merged_data['time_step'].isin(train_steps).values, dtype=torch.bool)
    val_mask = torch.tensor(merged_data['time_step'].isin(val_steps).values, dtype=torch.bool)
    test_mask = torch.tensor(merged_data['time_step'].isin(test_steps).values, dtype=torch.bool)
    
    # 过滤掉unknown标签
    known_labels = (labels != 2)
    train_mask = train_mask & torch.tensor(known_labels, dtype=torch.bool)
    val_mask = val_mask & torch.tensor(known_labels, dtype=torch.bool)
    test_mask = test_mask & torch.tensor(known_labels, dtype=torch.bool)
    
    print(f"数据统计:")
    print(f"总节点数: {len(labels)}")
    print(f"有标签节点数: {np.sum(known_labels)}")
    print(f"训练集节点数: {torch.sum(train_mask).item()}")
    print(f"验证集节点数: {torch.sum(val_mask).item()}")
    print(f"测试集节点数: {torch.sum(test_mask).item()}")
    
    # 创建PyTorch Geometric数据对象
    data = Data(
        x=torch.tensor(node_features, dtype=torch.float),
        edge_index=edge_index,
        y=torch.tensor(labels, dtype=torch.long),
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask
    )
    
    return data

def save_processed_data(data, save_path="./data/processed/elliptic_graph.pt"):
    """保存处理后的数据"""
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    torch.save(data, save_path)
    print(f"处理后的数据已保存至: {save_path}")

def main():
    """主处理函数"""
    print("=== 数据处理流程 ===")
    
    # 加载原始数据
    txs_features, txs_classes, txs_edgelist = load_elliptic_data()
    
    # 处理数据
    data = process_data(txs_features, txs_classes, txs_edgelist)
    
    # 保存处理后的数据
    save_processed_data(data)
    
    print("数据处理完成!")

if __name__ == "__main__":
    main()
