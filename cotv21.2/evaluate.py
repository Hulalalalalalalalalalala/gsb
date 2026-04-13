import torch
import argparse
import os
from data_utils import load_bitcoin_graph_data
from model import BitcoinFraudDetector
from train import evaluate as evaluate_model

def main():
    parser = argparse.ArgumentParser(description='评估Bitcoin地址风险识别模型')
    parser.add_argument('--model-path', type=str, default='models/bitcoin_fraud_detector.pth', help='模型路径')
    parser.add_argument('--split', type=str, default='test', choices=['val', 'test', 'all'], help='评估哪个数据集')
    parser.add_argument('--no-cuda', action='store_true', help='不使用CUDA')
    
    args = parser.parse_args()
    
    print("=== Bitcoin地址风险识别模型评估 ===")
    
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
    print(f"模型加载成功: {args.model_path}")
    
    # 选择评估集
    if args.split == 'val':
        mask = data.val_mask
        print(f"\n评估验证集...")
    elif args.split == 'test':
        mask = data.test_mask
        print(f"\n评估测试集...")
    else:  # all
        mask = torch.ones(data.num_nodes, dtype=torch.bool)
        print(f"\n评估全量数据...")
    
    # 评估
    metrics = evaluate_model(model, data, mask, device)
    
    # 打印结果
    print(f"\n评估结果 ({args.split}集):")
    print(f"{'='*50}")
    print(f"{'指标':<15} {'值':<10}")
    print(f"{'='*50}")
    for metric, value in metrics.items():
        if metric != 'loss':
            print(f"{metric.upper():<15} {value:<10.4f}")
    print(f"{'='*50}")
    
    # 额外统计信息
    num_samples = mask.sum().item()
    num_positive = data.y[mask].sum().item()
    print(f"\n样本统计:")
    print(f"  总样本数: {num_samples}")
    print(f"  正样本(欺诈): {num_positive} ({num_positive/num_samples:.2%})")
    print(f"  负样本(正常): {num_samples - num_positive} ({(num_samples - num_positive)/num_samples:.2%})")

if __name__ == "__main__":
    main()
