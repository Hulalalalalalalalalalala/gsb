import torch
import torch.nn.functional as F
import argparse
import os
import pandas as pd
import numpy as np
from tqdm import tqdm

from data_utils import load_bitcoin_graph_data
from model import BitcoinFraudDetector

def main():
    parser = argparse.ArgumentParser(description='Bitcoin地址风险识别推理脚本')
    parser.add_argument('--model-path', type=str, default='models/bitcoin_fraud_detector.pth', help='模型路径')
    parser.add_argument('--split', type=str, default='test', choices=['test', 'all'], help='推理数据集: test(测试集) 或 all(全量数据)')
    parser.add_argument('--output', type=str, default='predictions.csv', help='输出结果文件路径')
    parser.add_argument('--threshold', type=float, default=0.5, help='分类阈值')
    parser.add_argument('--no-cuda', action='store_true', help='不使用CUDA')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')
    
    args = parser.parse_args()
    
    print("=== Bitcoin地址风险识别推理 ===")
    
    # 设备配置
    device = torch.device('cuda' if torch.cuda.is_available() and not args.no_cuda else 'cpu')
    print(f"使用设备: {device}")
    
    # 检查模型文件
    if not os.path.exists(args.model_path):
        print(f"错误: 模型文件不存在: {args.model_path}")
        print("请先运行训练脚本: python train.py")
        return
    
    # 加载数据
    data = load_bitcoin_graph_data()
    
    # 加载地址信息
    address_df = pd.read_csv('data/addresses.csv')
    
    # 加载模型
    checkpoint = torch.load(args.model_path, map_location=device, weights_only=False)
    model_args = checkpoint['args']
    
    model = BitcoinFraudDetector(
        in_channels=data.num_features,
        hidden_channels=model_args.get('hidden_channels', 128),
        num_layers=model_args.get('num_layers', 2),
        dropout=model_args.get('dropout', 0.5)
    ).to(device)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    print(f"模型加载成功: {args.model_path}")
    
    # 选择推理数据
    if args.split == 'test':
        mask = data.test_mask
        print(f"\n对测试集进行推理...")
    else:
        mask = torch.ones(data.num_nodes, dtype=torch.bool)
        print(f"\n对全量数据进行推理...")
    
    # 执行推理
    print("正在执行推理...")
    with torch.no_grad():
        out = model(data.x.to(device), data.edge_index.to(device))
        probs = F.softmax(out, dim=1)[:, 1].cpu().numpy()
        preds = (probs >= args.threshold).astype(int)
    
    # 提取结果
    indices = torch.where(mask)[0].numpy()
    results = []
    
    for idx in tqdm(indices, desc="整理结果", disable=not args.verbose):
        addr_info = address_df.iloc[idx]
        results.append({
            'address': addr_info['address'],
            'true_label': addr_info['is_fraud'],
            'predicted_label': preds[idx],
            'fraud_probability': round(probs[idx], 4),
            'risk_level': get_risk_level(probs[idx])
        })
    
    # 转换为DataFrame
    results_df = pd.DataFrame(results)
    
    # 保存结果
    results_df.to_csv(args.output, index=False)
    print(f"\n推理结果已保存到: {args.output}")
    
    # 统计信息
    print(f"\n推理统计:")
    print(f"  总样本数: {len(results_df)}")
    print(f"  预测欺诈数: {(results_df['predicted_label'] == 1).sum()}")
    print(f"  预测正常数: {(results_df['predicted_label'] == 0).sum()}")
    
    # 风险等级分布
    risk_dist = results_df['risk_level'].value_counts()
    print(f"\n风险等级分布:")
    for level in ['High', 'Medium', 'Low']:
        count = risk_dist.get(level, 0)
        print(f"  {level}: {count} ({count/len(results_df):.2%})")
    
    # 如果有真实标签，显示准确率
    if 'true_label' in results_df.columns:
        correct = (results_df['predicted_label'] == results_df['true_label']).sum()
        accuracy = correct / len(results_df)
        print(f"\n准确率: {accuracy:.2%}")
        
        # 欺诈识别准确率
        fraud_mask = results_df['true_label'] == 1
        if fraud_mask.sum() > 0:
            fraud_correct = (results_df['predicted_label'][fraud_mask] == results_df['true_label'][fraud_mask]).sum()
            fraud_accuracy = fraud_correct / fraud_mask.sum()
            print(f"欺诈识别准确率: {fraud_accuracy:.2%}")
    
    print("\n推理完成！")

def get_risk_level(prob):
    """根据概率确定风险等级"""
    if prob >= 0.7:
        return 'High'
    elif prob >= 0.3:
        return 'Medium'
    else:
        return 'Low'

if __name__ == "__main__":
    main()
