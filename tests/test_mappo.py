import torch
import pytest
from src.agents.gat_layer import GraphAttentionLayer
from src.agents.mappo_agent import MAPPOActor, MAPPOCritic, MAPPOAgent
from src.env.traffic_env import VehicleState


def test_gat_layer_forward():
    gat = GraphAttentionLayer(in_features=4, out_features=16)
    ego = torch.randn(2, 4)  # batch_size=2, state_dim=4
    neighbors = torch.randn(2, 3, 4)  # batch_size=2, 3 neighbors, state_dim=4

    output = gat(ego, neighbors)
    assert output.shape == (2, 16)


def test_mappo_actor_forward():
    actor = MAPPOActor(state_dim=6, neighbor_dim=4, hidden_dim=32)
    ego = torch.randn(2, 6)
    neighbors = torch.randn(2, 3, 4)

    mean, std, comm_logit = actor(ego, neighbors)
    assert mean.shape == (2, 1)
    assert std.shape == (2, 1)
    assert comm_logit.shape == (2, 1)


def test_mappo_critic_forward():
    critic = MAPPOCritic(global_state_dim=24, hidden_dim=64)
    global_state = torch.randn(2, 24)
    value = critic(global_state)
    assert value.shape == (2, 1)


def test_mappo_agent_compute_action():
    agent = MAPPOAgent("v_N")
    vstate = VehicleState("v_N", x=0.0, y=30.0, vx=0.0, vy=-8.0)
    acc, msgs = agent.compute_action(vstate, [], ["v_N", "v_S"], current_step=1)

    assert isinstance(acc, float)
    assert isinstance(msgs, list)
