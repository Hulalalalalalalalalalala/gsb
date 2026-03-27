import torch
import torch.nn.functional as F
import argparse
import os
import numpy as np
from train import GraphSAGE

def load_model(model_path="./models/graphsage_best.pt", in_channels=165):
    """加载训练好的模型"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"模型文件不存在: {model_path}. 请先运行train.py训练模型")
    
    hidden_channels = 64
    out_channels = 2
    
    model = GraphSAGE(in_channels, hidden_channels, out_channels)
    model.load_state_dict(torch.load(model_path))
    model.eval()
    
    return model

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

def main():
    """推理主函数"""
    parser = argparse.ArgumentParser(description="Bitcoin地址风险识别推理脚本")
    parser.add_argument("--split", type=str, default="test", choices=["train", "val", "test", "all"],
                        help="要推理的数据集划分 (train/val/test/all)")
    parser.add_argument("--model-path", type=str, default="./models/graphsage_best.pt",
                        help="模型文件路径")
    parser.add_argument("--data-path", type=str, default="./data/processed/elliptic_graph.pt",
                        help="处理后的数据路径")
    parser.add_argument("--output-file", type=str, default="./predictions.csv",
                        help="预测结果输出文件")
    
    args = parser.parse_args()
    
    print("=== Bitcoin地址风险识别推理 ===")
    print(f"数据集划分: {args.split}")
    print(f"模型路径: {args.model_path}")
    print(f"数据路径: {args.data_path}")
    
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用设备: {device}")
    
    # 加载数据和模型
    data = load_data(args.data_path)
    data = data.to(device)
    
    model = load_model(args.model_path, in_channels=data.num_features)
    model = model.to(device)
    
    # 确定要推理的掩码
    if args.split == "train":
        mask = data.train_mask
    elif args.split == "val":
        mask = data.val_mask
    elif args.split == "test":
        mask = data.test_mask
    else:  # all
        mask = torch.ones(data.num_nodes, dtype=torch.bool, device=device)
    
    print(f"推理节点数: {mask.sum().item()}")
    
    # 推理
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        probs = F.softmax(out, dim=1)[:, 1].cpu().numpy()
        preds = out.argmax(dim=1).cpu().numpy()
    
    # 只保留掩码内的结果
    mask_np = mask.cpu().numpy()
    results = {
        'probability': probs[mask_np],
        'prediction': preds[mask_np]
    }
    
    # 打印部分结果
    print("\n=== 推理结果预览 (前10个) ===")
    print("概率 | 预测 (1=风险, 0=正常)")
    print("-" * 50)
    for prob, pred in zip(results['probability'][:10], results['prediction'][:10]):
        print(f"{prob:.4f} | {pred}")
    
    # 保存结果
    import pandas as pd
    results_df = pd.DataFrame({
        'probability': results['probability'],
        'prediction': results['prediction']
    })
    
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)
    results_df.to_csv(args.output_file, index=False)
    print(f"\n完整预测结果已保存至: {args.output_file}")
    
    # 打印统计信息
    risk_count = np.sum(results['prediction'] == 1)
    normal_count = np.sum(results['prediction'] == 0)
    print(f"\n预测统计:")
    print(f"  风险地址数: {risk_count} ({risk_count/len(results['prediction'])*100:.2f}%)")
    print(f"  正常地址数: {normal_count} ({normal_count/len(results['prediction'])*100:.2f}%)")

if __name__ == "__main__":
    main()
