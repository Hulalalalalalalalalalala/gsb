import os
import numpy as np
import pandas as pd
import requests
import zipfile
import io
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
import networkx as nx
import torch
from torch_geometric.data import Data
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def download_file(url, dest_path):
    """下载文件带进度条"""
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    with open(dest_path, 'wb') as f, tqdm(
        desc=os.path.basename(dest_path),
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                pbar.update(len(chunk))

def download_kaggle_bitcoin_dataset():
    """尝试下载公开的Bitcoin数据集"""
    print("尝试下载Bitcoin交易数据集...")
    
    # 使用Kaggle的Bitcoin交易数据集的镜像源
    urls = [
        "https://github.com/elliotcoindata/bitcoin-data/raw/master/transactions_sample.csv",
        "https://raw.githubusercontent.com/bitcoin/bitcoin/master/contrib/seeds/nodes_main.txt"
    ]
    
    for url in urls:
        try:
            print(f"尝试从 {url} 下载...")
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print("下载成功！")
                return True
        except Exception as e:
            print(f"下载失败: {e}")
            continue
    
    print("所有下载源均失败，将生成模拟数据集。")
    return False

def generate_simulated_bitcoin_data(num_addresses=5000, num_transactions=20000, fraud_ratio=0.15):
    """生成模拟的Bitcoin交易数据"""
    print("\n=== 生成模拟Bitcoin交易数据集 ===")
    
    # 1. 生成地址信息
    addresses = [f'bc1q{i:06x}' for i in range(num_addresses)]
    is_fraud = np.random.choice([0, 1], size=num_addresses, p=[1-fraud_ratio, fraud_ratio])
    
    # 地址特征：余额、交易次数、平均交易金额、活跃天数
    np.random.seed(42)
    balance = np.random.lognormal(mean=0, sigma=3, size=num_addresses)
    tx_count = np.random.poisson(lam=5, size=num_addresses) + 1
    avg_tx_value = np.random.lognormal(mean=2, sigma=2, size=num_addresses)
    active_days = np.random.randint(1, 365, size=num_addresses)
    
    # 欺诈地址通常有异常模式
    fraud_mask = is_fraud == 1
    balance[fraud_mask] *= 2
    tx_count[fraud_mask] = np.random.poisson(lam=20, size=fraud_mask.sum())
    
    address_df = pd.DataFrame({
        'address': addresses,
        'is_fraud': is_fraud,
        'balance': balance,
        'tx_count': tx_count,
        'avg_tx_value': avg_tx_value,
        'active_days': active_days,
        'first_seen': np.random.randint(1609459200, 1709459200, size=num_addresses)  # 2021-2024
    })
    
    # 2. 生成交易信息
    from_indices = np.random.randint(0, num_addresses, size=num_transactions)
    to_indices = np.random.randint(0, num_addresses, size=num_transactions)
    
    # 确保没有自交易
    same_idx = from_indices == to_indices
    to_indices[same_idx] = (to_indices[same_idx] + 1) % num_addresses
    
    tx_values = np.random.lognormal(mean=1, sigma=2, size=num_transactions)
    tx_timestamps = np.random.randint(1609459200, 1709459200, size=num_transactions)
    
    # 欺诈地址之间的交易更多
    fraud_indices = np.where(fraud_mask)[0]
    if len(fraud_indices) > 1:
        num_fraud_tx = int(num_transactions * 0.3)
        fraud_from = np.random.choice(fraud_indices, size=num_fraud_tx)
        fraud_to = np.random.choice(fraud_indices, size=num_fraud_tx)
        same_idx = fraud_from == fraud_to
        fraud_to[same_idx] = np.random.choice(fraud_indices, size=same_idx.sum())
        
        from_indices[-num_fraud_tx:] = fraud_from
        to_indices[-num_fraud_tx:] = fraud_to
    
    transaction_df = pd.DataFrame({
        'from_address': [addresses[i] for i in from_indices],
        'to_address': [addresses[i] for i in to_indices],
        'value': tx_values,
        'timestamp': tx_timestamps
    })
    
    # 按时间排序
    transaction_df = transaction_df.sort_values('timestamp').reset_index(drop=True)
    
    print(f"生成了 {num_addresses} 个地址，{num_transactions} 笔交易")
    print(f"欺诈地址比例: {is_fraud.mean():.2%}")
    
    return address_df, transaction_df

def build_graph_from_data(address_df, transaction_df):
    """从DataFrame构建PyTorch Geometric图"""
    print("\n=== 构建图结构 ===")
    
    # 创建地址到索引的映射
    address_to_idx = {addr: i for i, addr in enumerate(address_df['address'])}
    
    # 构建边索引
    edge_index = []
    edge_attr = []
    
    for _, row in tqdm(transaction_df.iterrows(), total=len(transaction_df), desc="处理交易"):
        from_idx = address_to_idx.get(row['from_address'])
        to_idx = address_to_idx.get(row['to_address'])
        
        if from_idx is not None and to_idx is not None:
            # 添加双向边（交易是有向的，但GraphSAGE可以使用双向）
            edge_index.append([from_idx, to_idx])
            edge_index.append([to_idx, from_idx])
            
            # 边特征：交易金额
            edge_attr.append([row['value']])
            edge_attr.append([row['value']])
    
    edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(edge_attr, dtype=torch.float)
    
    # 节点特征
    feature_cols = ['balance', 'tx_count', 'avg_tx_value', 'active_days']
    X = address_df[feature_cols].values
    
    # 标准化特征
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    x = torch.tensor(X_scaled, dtype=torch.float)
    
    # 标签
    y = torch.tensor(address_df['is_fraud'].values, dtype=torch.long)
    
    # 时间信息用于划分数据集
    timestamps = torch.tensor(address_df['first_seen'].values, dtype=torch.long)
    
    # 创建PyG Data对象
    data = Data(
        x=x,
        edge_index=edge_index,
        edge_attr=edge_attr,
        y=y,
        timestamps=timestamps
    )
    
    print(f"节点数: {data.num_nodes}")
    print(f"边数: {data.num_edges}")
    print(f"特征维度: {data.num_features}")
    
    return data, scaler

def split_by_time(data, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
    """按时间划分数据集"""
    print(f"\n=== 按时间划分数据集 (train:{train_ratio}, val:{val_ratio}, test:{test_ratio}) ===")
    
    # 根据时间戳排序节点
    sorted_indices = torch.argsort(data.timestamps)
    n = len(sorted_indices)
    
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    train_indices = sorted_indices[:train_end]
    val_indices = sorted_indices[train_end:val_end]
    test_indices = sorted_indices[val_end:]
    
    # 创建掩码
    train_mask = torch.zeros(n, dtype=torch.bool)
    val_mask = torch.zeros(n, dtype=torch.bool)
    test_mask = torch.zeros(n, dtype=torch.bool)
    
    train_mask[train_indices] = True
    val_mask[val_indices] = True
    test_mask[test_indices] = True
    
    data.train_mask = train_mask
    data.val_mask = val_mask
    data.test_mask = test_mask
    
    print(f"训练集: {train_mask.sum().item()} 节点 ({train_mask.sum().item()/n:.2%})")
    print(f"验证集: {val_mask.sum().item()} 节点 ({val_mask.sum().item()/n:.2%})")
    print(f"测试集: {test_mask.sum().item()} 节点 ({test_mask.sum().item()/n:.2%})")
    
    # 检查各集的欺诈比例
    print(f"\n欺诈比例分布:")
    print(f"  训练集: {data.y[train_mask].sum().item() / train_mask.sum().item():.2%}")
    print(f"  验证集: {data.y[val_mask].sum().item() / val_mask.sum().item():.2%}")
    print(f"  测试集: {data.y[test_mask].sum().item() / test_mask.sum().item():.2%}")
    
    return data

def load_bitcoin_graph_data(force_regenerate=False):
    """主函数：加载或生成Bitcoin图数据"""
    
    data_path = os.path.join(DATA_DIR, 'bitcoin_graph_data.pt')
    address_path = os.path.join(DATA_DIR, 'addresses.csv')
    transaction_path = os.path.join(DATA_DIR, 'transactions.csv')
    
    # 检查是否已有缓存数据
    if not force_regenerate and os.path.exists(data_path):
        print(f"加载已缓存的图数据: {data_path}")
        data = torch.load(data_path, weights_only=False)
        return data
    
    # 尝试下载真实数据，失败则生成模拟数据
    download_success = download_kaggle_bitcoin_dataset()
    
    if download_success and os.path.exists(address_path) and os.path.exists(transaction_path):
        print("加载真实数据集...")
        address_df = pd.read_csv(address_path)
        transaction_df = pd.read_csv(transaction_path)
    else:
        print("使用模拟数据集...")
        address_df, transaction_df = generate_simulated_bitcoin_data()
        
        # 保存模拟数据
        address_df.to_csv(address_path, index=False)
        transaction_df.to_csv(transaction_path, index=False)
        print(f"模拟数据已保存到 {DATA_DIR}")
    
    # 构建图
    data, scaler = build_graph_from_data(address_df, transaction_df)
    
    # 按时间划分数据集
    data = split_by_time(data)
    
    # 保存数据
    torch.save(data, data_path)
    print(f"\n图数据已缓存到: {data_path}")
    
    return data

if __name__ == "__main__":
    data = load_bitcoin_graph_data(force_regenerate=True)
    print("\n数据加载完成！")
    print(f"训练节点数: {data.train_mask.sum().item()}")
    print(f"验证节点数: {data.val_mask.sum().item()}")
    print(f"测试节点数: {data.test_mask.sum().item()}")
