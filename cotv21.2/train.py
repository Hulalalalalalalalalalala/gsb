import os
import torch
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm
from sklearn.metrics import roc_auc_score, f1_score, precision_score, recall_score
import argparse

from data_utils import load_bitcoin_graph_data
from model import BitcoinFraudDetector

def train_epoch(model, data, optimizer, device):
    model.train()
    optimizer.zero_grad()
    
    out = model(data.x.to(device), data.edge_index.to(device))
    loss = F.cross_entropy(out[data.train_mask], data.y[data.train_mask].to(device))
    
    loss.backward()
    optimizer.step()
    
    return loss.item()

@torch.no_grad()
def evaluate(model, data, mask, device):
    model.eval()
    out = model(data.x.to(device), data.edge_index.to(device))
    logits = out[mask]
    labels = data.y[mask].cpu().numpy()
    
    probs = F.softmax(logits, dim=1)[:, 1].cpu().numpy()
    preds = logits.argmax(dim=1).cpu().numpy()
    
    # 计算指标
    try:
        auc = roc_auc_score(labels, probs)
    except ValueError:
        auc = 0.5
    
    f1 = f1_score(labels, preds, zero_division=0)
    precision = precision_score(labels, preds, zero_division=0)
    recall = recall_score(labels, preds, zero_division=0)
    
    loss = F.cross_entropy(out[mask], data.y[mask].to(device)).item()
    
    return {
        'loss': loss,
        'auc': auc,
        'f1': f1,
        'precision': precision,
        'recall': recall
    }

def train(args):
    print("=== Bitcoin地址风险识别模型训练 ===")
    
    # 设备配置
    device = torch.device('cuda' if torch.cuda.is_available() and not args.no_cuda else 'cpu')
    print(f"使用设备: {device}")
    
    # 加载数据
    data = load_bitcoin_graph_data()
    
    # 初始化模型
    model = BitcoinFraudDetector(
        in_channels=data.num_features,
        hidden_channels=args.hidden_channels,
        num_layers=args.num_layers,
        dropout=args.dropout
    ).to(device)
    
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    
    # 学习率调度器
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='max', factor=0.5, patience=10, verbose=True
    )
    
    # 训练循环
    best_val_auc = 0
    best_model_state = None
    no_improve = 0
    
    print("\n开始训练...")
    for epoch in range(1, args.epochs + 1):
        train_loss = train_epoch(model, data, optimizer, device)
        
        # 评估
        train_metrics = evaluate(model, data, data.train_mask, device)
        val_metrics = evaluate(model, data, data.val_mask, device)
        
        # 学习率调度
        scheduler.step(val_metrics['auc'])
        
        # 保存最佳模型
        if val_metrics['auc'] > best_val_auc:
            best_val_auc = val_metrics['auc']
            best_model_state = model.state_dict().copy()
            no_improve = 0
        else:
            no_improve += 1
        
        # 早停
        if no_improve >= args.patience:
            print(f"\n早停触发！{args.patience}轮无提升。")
            break
        
        # 打印进度
        if epoch % args.print_interval == 0 or epoch == 1:
            print(f"\nEpoch {epoch}/{args.epochs}")
            print(f"训练集 - Loss: {train_metrics['loss']:.4f}, AUC: {train_metrics['auc']:.4f}, F1: {train_metrics['f1']:.4f}")
            print(f"验证集 - Loss: {val_metrics['loss']:.4f}, AUC: {val_metrics['auc']:.4f}, F1: {val_metrics['f1']:.4f}")
    
    # 加载最佳模型
    model.load_state_dict(best_model_state)
    
    # 最终评估
    print("\n=== 最终评估 ===")
    test_metrics = evaluate(model, data, data.test_mask, device)
    
    print("\n验证集指标:")
    val_metrics = evaluate(model, data, data.val_mask, device)
    for metric, value in val_metrics.items():
        if metric != 'loss':
            print(f"  {metric.upper()}: {value:.4f}")
    
    print("\n测试集指标:")
    for metric, value in test_metrics.items():
        if metric != 'loss':
            print(f"  {metric.upper()}: {value:.4f}")
    
    # 保存模型
    os.makedirs('models', exist_ok=True)
    torch.save({
        'model_state_dict': best_model_state,
        'args': vars(args),
        'val_metrics': val_metrics,
        'test_metrics': test_metrics
    }, 'models/bitcoin_fraud_detector.pth')
    
    print(f"\n模型已保存到: models/bitcoin_fraud_detector.pth")
    
    return val_metrics, test_metrics

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='训练Bitcoin地址风险识别模型')
    
    parser.add_argument('--epochs', type=int, default=100, help='训练轮数')
    parser.add_argument('--hidden-channels', type=int, default=128, help='隐藏层维度')
    parser.add_argument('--num-layers', type=int, default=2, help='GraphSAGE层数')
    parser.add_argument('--dropout', type=float, default=0.5, help='Dropout率')
    parser.add_argument('--lr', type=float, default=0.001, help='学习率')
    parser.add_argument('--weight-decay', type=float, default=1e-4, help='权重衰减')
    parser.add_argument('--patience', type=int, default=20, help='早停耐心值')
    parser.add_argument('--print-interval', type=int, default=10, help='打印间隔')
    parser.add_argument('--no-cuda', action='store_true', help='不使用CUDA')
    
    args = parser.parse_args()
    
    val_metrics, test_metrics = train(args)
