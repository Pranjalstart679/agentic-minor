import torch
import torch.nn as nn
import torch.nn.functional as F


class GraphAttentionLayer(nn.Module):
    """
    Graph Attention Network (GAT) layer for processing dynamic V2X neighbor state features:
    Computes spatial attention weights alpha_ij between ego vehicle i and neighbor vehicles j.
    """

    def __init__(self, in_features: int, out_features: int, dropout: float = 0.1, alpha: float = 0.2):
        super(GraphAttentionLayer, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.dropout = dropout
        self.alpha = alpha

        # Linear projection weight W
        self.W = nn.Parameter(torch.empty(size=(in_features, out_features)))
        nn.init.xavier_uniform_(self.W.data, gain=1.414)

        # Attention mechanism parameter a
        self.a = nn.Parameter(torch.empty(size=(2 * out_features, 1)))
        nn.init.xavier_uniform_(self.a.data, gain=1.414)

        self.leakyrelu = nn.LeakyReLU(self.alpha)

    def forward(self, ego_features: torch.Tensor, neighbor_features: torch.Tensor) -> torch.Tensor:
        """
        ego_features: [batch_size, in_features]
        neighbor_features: [batch_size, num_neighbors, in_features]
        Returns: aggregated neighbor context representation [batch_size, out_features]
        """
        batch_size, num_neighbors, _ = neighbor_features.shape

        if num_neighbors == 0:
            return torch.zeros(batch_size, self.out_features, device=ego_features.device)

        # Linear projections
        h_ego = torch.matmul(ego_features, self.W)  # [batch_size, out_features]
        h_neighbors = torch.matmul(neighbor_features, self.W)  # [batch_size, num_neighbors, out_features]

        # Expand ego features to match neighbor count for pair-wise concatenation
        h_ego_expanded = h_ego.unsqueeze(1).repeat(1, num_neighbors, 1)  # [batch_size, num_neighbors, out_features]

        # Concatenate [h_i || h_j]
        a_input = torch.cat([h_ego_expanded, h_neighbors], dim=-1)  # [batch_size, num_neighbors, 2 * out_features]

        # Compute unnormalized attention scores e_ij
        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(-1))  # [batch_size, num_neighbors]

        # Softmax over neighbor dimension
        alpha_weights = F.softmax(e, dim=-1)  # [batch_size, num_neighbors]
        alpha_weights = F.dropout(alpha_weights, p=self.dropout, training=self.training)

        # Weighted aggregation
        aggregated = torch.bmm(alpha_weights.unsqueeze(1), h_neighbors).squeeze(1)  # [batch_size, out_features]
        return aggregated
