import math
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
from src.agents.base_agent import BaseCooperativeAgent
from src.agents.gat_layer import GraphAttentionLayer
from src.env.traffic_env import VehicleState
from src.env.comm_channel import Message, PriorityLevel


class MAPPOActor(nn.Module):
    """
    MAPPO Decentralized Actor Policy Network with Graph Attention over neighbor states.
    Outputs: Continuous Acceleration Action (Gaussian) & Discrete Communication Flag (Bernoulli).
    """

    def __init__(self, state_dim: int = 6, neighbor_dim: int = 4, hidden_dim: int = 64):
        super(MAPPOActor, self).__init__()
        self.gat = GraphAttentionLayer(in_features=neighbor_dim, out_features=hidden_dim)

        self.ego_encoder = nn.Linear(state_dim, hidden_dim)
        self.fc_shared = nn.Linear(hidden_dim * 2, hidden_dim)

        # Acceleration Action Head (Gaussian)
        self.accel_mean = nn.Linear(hidden_dim, 1)
        self.accel_log_std = nn.Parameter(torch.zeros(1))

        # Communication Decision Head (Bernoulli Logit)
        self.comm_logit = nn.Linear(hidden_dim, 1)

    def forward(
        self, ego_state: torch.Tensor, neighbor_states: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        ego_state: [batch_size, 6]
        neighbor_states: [batch_size, num_neighbors, 4]
        Returns: (accel_mean, accel_std, comm_logit)
        """
        h_ego = F.relu(self.ego_encoder(ego_state))
        h_gat = self.gat(ego_state[:, :4], neighbor_states)

        h_combined = torch.cat([h_ego, h_gat], dim=-1)
        h_shared = F.relu(self.fc_shared(h_combined))

        mean = torch.tanh(self.accel_mean(h_shared)) * 3.0  # Scale acceleration
        std = torch.exp(self.accel_log_std).expand_as(mean)
        comm_logit = self.comm_logit(h_shared)

        return mean, std, comm_logit


class MAPPOCritic(nn.Module):
    """
    Centralized Critic Network evaluating global multi-agent state value V(S_global).
    """

    def __init__(self, global_state_dim: int = 24, hidden_dim: int = 128):
        super(MAPPOCritic, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(global_state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, global_state: torch.Tensor) -> torch.Tensor:
        return self.net(global_state)


class MAPPOAgent(BaseCooperativeAgent):
    """
    Neural Multi-Agent Proximal Policy Optimization (MAPPO) Agent:
    - Uses MAPPOActor network for decentralized acceleration control and learned communication decisions.
    """

    def __init__(self, vehicle_id: str, actor_net: Optional[MAPPOActor] = None):
        super().__init__(vehicle_id)
        self.actor = actor_net or MAPPOActor()
        self.actor.eval()

    def compute_action(
        self,
        self_state: VehicleState,
        received_messages: List[Message],
        all_vehicle_ids: List[str],
        current_step: int,
    ) -> Tuple[float, List[Message]]:
        # 1. Update neighbor state representation from received messages
        for msg in received_messages:
            if msg.receiver_id in [self.vehicle_id, "broadcast"]:
                self.known_neighbors[msg.sender_id] = {
                    "pos": msg.content.get("pos", (0.0, 0.0)),
                    "vel": msg.content.get("vel", (0.0, 0.0)),
                    "timestamp": msg.timestamp,
                }

        # 2. Prepare PyTorch tensors for ego & neighbor states
        ego_tensor = torch.tensor(
            [[self_state.x, self_state.y, self_state.vx, self_state.vy, self_state.ax, self_state.ay]],
            dtype=torch.float32,
        )

        neighbor_features = []
        for nid in all_vehicle_ids:
            if nid != self.vehicle_id:
                if nid in self.known_neighbors:
                    nx, ny = self.known_neighbors[nid]["pos"]
                    nvx, nvy = self.known_neighbors[nid]["vel"]
                    # Relative position and velocity features
                    neighbor_features.append([nx - self_state.x, ny - self_state.y, nvx - self_state.vx, nvy - self_state.vy])
                else:
                    neighbor_features.append([0.0, 0.0, 0.0, 0.0])

        if neighbor_features:
            neighbor_tensor = torch.tensor([neighbor_features], dtype=torch.float32)
        else:
            neighbor_tensor = torch.zeros((1, 0, 4), dtype=torch.float32)

        # 3. Neural Policy Forward Pass
        with torch.no_grad():
            mean, std, comm_logit = self.actor(ego_tensor, neighbor_tensor)
            action_accel = float(mean.item())
            comm_prob = float(torch.sigmoid(comm_logit).item())

        # 4. Generate outgoing messages if learned communication decision is active
        outgoing_msgs = []
        if comm_prob > 0.5 or current_step == 1:
            for target_id in all_vehicle_ids:
                if target_id != self.vehicle_id:
                    msg = Message(
                        priority=PriorityLevel.NORMAL,
                        sender_id=self.vehicle_id,
                        receiver_id=target_id,
                        timestamp=current_step,
                        content={"pos": (self_state.x, self_state.y), "vel": (self_state.vx, self_state.vy)},
                    )
                    outgoing_msgs.append(msg)

        return action_accel, outgoing_msgs
