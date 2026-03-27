import numpy as np
import pandas as pd
import torch
from torch_geometric.data import Data
import os
import networkx as nx

def generate_synthetic_bitcoin_data(num_nodes=10000, num_edges=50000, num_features=165, random_seed=42):
    """生成合成的Bitcoin交易数据用于测试"""
    np.random.seed(random_seed)
    
    print("生成合成Bitcoin交易数据...")
    
    # 生成交易特征
    node_features = np.random.randn(num_nodes, num_features)
    
    # 生成时间步 (模拟真实数据的时间结构)
    time_steps = np.random.randint(1, 50, size=num_nodes)
    
    # 生成标签 (1=风险地址, 0=正常地址, 2=未标注)
    labels = np.random.choice([0, 1, 2], size=num_nodes, p=[0.7, 0.15, 0.15])
    
    # 生成交易边 (模拟交易网络)
    edges = []
    for _ in range(num_edges):
        # 优先连接原则 - 新节点更可能连接到已有节点
        if np.random.rand() < 0.7 and len(edges) > 0:
            # 优先连接到已有节点
            target = np.random.randint(0, num_nodes)
            source = np.random.randint(0, num_nodes)
        else:
            # 随机连接
            source = np.random.randint(0, num_nodes)
            target = np.random.randint(0, num_nodes)
        
        if source != target:
            edges.append([source, target])
    
    edges = np.array(edges)
    
    print(f"合成数据统计:")
    print(f"  节点数: {num_nodes}")
    print(f"  边数: {len(edges)}")
    print(f"  特征数: {num_features}")
    print(f"  风险地址比例: {np.sum(labels == 1)/num_nodes:.2%}")
    print(f"  正常地址比例: {np.sum(labels == 0)/num_nodes:.2%}")
    print(f"  未标注比例: {np.sum(labels == 2)/num_nodes:.2%}")
    
    return node_features, labels, edges, time_steps

def create_graph_data(node_features, labels, edges, time_steps):
    """从合成数据创建图结构数据"""
    print("\n构建图结构数据...")
    
    # 按时间步分割数据
    unique_time_steps = sorted(np.unique(time_steps))
    total_steps = len(unique_time_steps)
    
    # 80%训练，10%验证，10%测试
    train_steps = unique_time_steps[:int(total_steps * 0.8)]
    val_steps = unique_time_steps[int(total_steps * 0.8):int(total_steps * 0.9)]
    test_steps = unique_time_steps[int(total_steps * 0.9):]
    
    print(f"时间步分布:")
    print(f"  训练时间步: {len(train_steps)}")
    print(f"  验证时间步: {len(val_steps)}")
    print(f"  测试时间步: {len(test_steps)}")
    
    # 标准化特征
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    node_features = scaler.fit_transform(node_features)
    
    # 创建边索引
    edge_index = torch.tensor(edges.T, dtype=torch.long)
    
    # 创建掩码
    train_mask = torch.tensor(np.isin(time_steps, train_steps), dtype=torch.bool)
    val_mask = torch.tensor(np.isin(time_steps, val_steps), dtype=torch.bool)
    test_mask = torch.tensor(np.isin(time_steps, test_steps), dtype=torch.bool)
    
    # 过滤掉未标注的节点
    known_labels = (labels != 2)
    train_mask = train_mask & torch.tensor(known_labels, dtype=torch.bool)
    val_mask = val_mask & torch.tensor(known_labels, dtype=torch.bool)
    test_mask = test_mask & torch.tensor(known_labels, dtype=torch.bool)
    
    print(f"数据统计:")
    print(f"  总节点数: {len(labels)}")
    print(f"  有标签节点数: {np.sum(known_labels)}")
    print(f"  训练集节点数: {torch.sum(train_mask).item()}")
    print(f"  验证集节点数: {torch.sum(val_mask).item()}")
    print(f"  测试集节点数: {torch.sum(test_mask).item()}")
    
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

def save_synthetic_data(data, save_dir="./data/synthetic"):
    """保存合成数据"""
    os.makedirs(save_dir, exist_ok=True)
    
    # 保存PyTorch格式
    torch.save(data, os.path.join(save_dir, "synthetic_graph.pt"))
    
    # 保存CSV格式以便查看
    pd.DataFrame(data.x.numpy()).to_csv(os.path.join(save_dir, "node_features.csv"), index=False)
    pd.DataFrame(data.edge_index.numpy().T, columns=['source', 'target']).to_csv(
        os.path.join(save_dir, "edges.csv"), index=False
    )
    pd.DataFrame({'label': data.y.numpy()}).to_csv(os.path.join(save_dir, "labels.csv"), index=False)
    
    print(f"\n合成数据已保存至: {save_dir}")
    print("  - synthetic_graph.pt (PyTorch格式)")
    print("  - node_features.csv (节点特征)")
    print("  - edges.csv (边列表)")
    print("  - labels.csv (标签)")

def main():
    """主函数"""
    print("=== 合成Bitcoin交易数据生成器 ===")
    print("此脚本生成合成数据用于测试Bitcoin地址风险识别模型")
    print("=" * 50)
    
    # 生成合成数据
    node_features, labels, edges, time_steps = generate_synthetic_bitcoin_data(
        num_nodes=5000,  # 较小规模以便快速测试
        num_edges=25000,
        num_features=165  # 与真实数据保持相同维度
    )
    
    # 构建图结构
    data = create_graph_data(node_features, labels, edges, time_steps)
    
    # 保存数据
    save_synthetic_data(data)
    
    print("\n合成数据生成完成!")
    print("\n使用建议:")
    print("1. 使用合成数据测试模型训练: python train.py --data-path ./data/synthetic/synthetic_graph.pt")
    print("2. 当真实数据下载成功后，再使用真实数据训练")
    print("3. 合成数据仅用于测试流程，真实性能需用真实数据验证")

if __name__ == "__main__":
    main()
