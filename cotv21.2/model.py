import torch
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv

class GraphSAGE(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels, out_channels, num_layers=2, dropout=0.5):
        super().__init__()
        
        self.dropout = dropout
        self.num_layers = num_layers
        
        self.convs = torch.nn.ModuleList()
        self.bns = torch.nn.ModuleList()
        
        # 输入层
        self.convs.append(SAGEConv(in_channels, hidden_channels))
        self.bns.append(torch.nn.BatchNorm1d(hidden_channels))
        
        # 隐藏层
        for _ in range(num_layers - 2):
            self.convs.append(SAGEConv(hidden_channels, hidden_channels))
            self.bns.append(torch.nn.BatchNorm1d(hidden_channels))
        
        # 输出层
        if num_layers >= 2:
            self.convs.append(SAGEConv(hidden_channels, out_channels))
        else:
            self.convs[0] = SAGEConv(in_channels, out_channels)
        
    def forward(self, x, edge_index):
        for i, conv in enumerate(self.convs[:-1]):
            x = conv(x, edge_index)
            if i < len(self.bns):
                x = self.bns[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.convs[-1](x, edge_index)
        return x
    
    def get_embeddings(self, x, edge_index):
        """获取节点嵌入"""
        for i, conv in enumerate(self.convs[:-1]):
            x = conv(x, edge_index)
            if i < len(self.bns):
                x = self.bns[i](x)
            x = F.relu(x)
        return x

class BitcoinFraudDetector(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels=128, num_layers=2, dropout=0.5):
        super().__init__()
        
        # 基础embedding层
        self.embedding_layer = torch.nn.Linear(in_channels, hidden_channels)
        
        # GraphSAGE编码器
        self.graphsage = GraphSAGE(
            in_channels=hidden_channels,
            hidden_channels=hidden_channels,
            out_channels=hidden_channels,
            num_layers=num_layers,
            dropout=dropout
        )
        
        # 分类头
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(hidden_channels, hidden_channels // 2),
            torch.nn.ReLU(),
            torch.nn.Dropout(dropout),
            torch.nn.Linear(hidden_channels // 2, 2)
        )
        
    def forward(self, x, edge_index):
        # 基础embedding
        x = self.embedding_layer(x)
        x = F.relu(x)
        
        # GraphSAGE编码
        x = self.graphsage(x, edge_index)
        
        # 分类
        logits = self.classifier(x)
        return logits
    
    def get_embeddings(self, x, edge_index):
        """获取最终节点嵌入"""
        x = self.embedding_layer(x)
        x = F.relu(x)
        return self.graphsage.get_embeddings(x, edge_index)
