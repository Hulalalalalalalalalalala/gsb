import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from torch_geometric.data import Data
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
import numpy as np
import os

class GraphSAGE(nn.Module):
    """GraphSAGE模型用于Bitcoin地址风险识别"""
    def __init__(self, in_channels, hidden_channels, out_channels, num_layers=2, dropout=0.5):
        super(GraphSAGE, self).__init__()
        
        self.convs = nn.ModuleList()
        self.convs.append(SAGEConv(in_channels, hidden_channels))
        
        for _ in range(num_layers - 2):
            self.convs.append(SAGEConv(hidden_channels, hidden_channels))
        
        self.convs.append(SAGEConv(hidden_channels, out_channels))
        self.dropout = dropout
        
    def forward(self, x, edge_index):
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            if i != len(self.convs) - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        return x

def load_data(data_path=None):
    """加载处理后的数据"""
    # 尝试多种数据路径
    possible_paths = [
        "./data/processed/elliptic_graph.pt",
        "./data/synthetic/synthetic_graph.pt",
        "./synthetic_graph.pt"
    ]
    
    if data_path:
        possible_paths = [data_path]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"加载数据: {path}")
            try:
                # PyTorch 2.6+ 兼容模式
                return torch.load(path, weights_only=False)
            except:
                # 旧版PyTorch兼容
                return torch.load(path)
    
    # 如果都不存在，生成合成数据
    print("未找到数据文件，正在生成合成数据...")
    from synthetic_data import generate_synthetic_bitcoin_data, create_graph_data
    node_features, labels, edges, time_steps = generate_synthetic_bitcoin_data(
        num_nodes=5000, num_edges=25000, num_features=165
    )
    data = create_graph_data(node_features, labels, edges, time_steps)
    
    # 保存合成数据
    os.makedirs("./data/synthetic", exist_ok=True)
    torch.save(data, "./data/synthetic/synthetic_graph.pt")
    print("合成数据已保存至: ./data/synthetic/synthetic_graph.pt")
    
    return data

def train():
    """主训练函数"""
    print("=== GraphSAGE Bitcoin地址风险识别训练 ===")
    
    # 加载数据
    data = load_data()
    print(f"数据加载完成: {data}")
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    data = data.to(device)
    
    # 模型参数
    in_channels = data.num_features
    hidden_channels = 64
    out_channels = 2  # 二分类: 风险(1) 或 正常(0)
    
    # 创建模型
    model = GraphSAGE(in_channels, hidden_channels, out_channels).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    criterion = nn.CrossEntropyLoss()
    
    print(f"模型结构:\n{model}")
    
    # 训练循环
    best_val_auc = 0
    best_model = None
    
    for epoch in range(1, 101):
        model.train()
        optimizer.zero_grad()
        
        out = model(data.x, data.edge_index)
        loss = criterion(out[data.train_mask], data.y[data.train_mask])
        
        loss.backward()
        optimizer.step()
        
        # 评估
        train_metrics = evaluate(model, data, data.train_mask)
        val_metrics = evaluate(model, data, data.val_mask)
        
        if val_metrics['auc'] > best_val_auc:
            best_val_auc = val_metrics['auc']
            best_model = model.state_dict().copy()
        
        if epoch % 10 == 0:
            print(f"Epoch {epoch:03d} | "
                  f"Train Loss: {loss.item():.4f} | "
                  f"Train AUC: {train_metrics['auc']:.4f} | "
                  f"Val AUC: {val_metrics['auc']:.4f}")
    
    # 加载最佳模型
    model.load_state_dict(best_model)
    
    # 在测试集上评估
    print("\n=== 测试集评估 ===")
    test_metrics = evaluate(model, data, data.test_mask)
    print_metrics(test_metrics, "测试集")
    
    # 保存模型
    os.makedirs("./models", exist_ok=True)
    torch.save(model.state_dict(), "./models/graphsage_best.pt")
    print(f"\n最佳模型已保存至: ./models/graphsage_best.pt")
    
    return model, test_metrics

def evaluate(model, data, mask):
    """评估模型性能"""
    model.eval()
    
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        probs = F.softmax(out, dim=1)[:, 1].cpu().numpy()
        preds = out.argmax(dim=1).cpu().numpy()
        labels = data.y.cpu().numpy()
    
    # 只评估掩码内的样本
    mask_np = mask.cpu().numpy()
    probs = probs[mask_np]
    preds = preds[mask_np]
    labels = labels[mask_np]
    
    # 计算指标
    auc = roc_auc_score(labels, probs)
    f1 = f1_score(labels, preds)
    precision = precision_score(labels, preds)
    recall = recall_score(labels, preds)
    
    return {
        'auc': auc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def print_metrics(metrics, name):
    """打印指标"""
    print(f"{name} 指标:")
    print(f"  AUC: {metrics['auc']:.4f}")
    print(f"  F1: {metrics['f1']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")

if __name__ == "__main__":
    train()
