---
name: mappo-gat-training
description: |
  Guide and operational procedures for training, evaluating, and checkpointing
  Multi-Agent PPO (MAPPO) with Graph Attention Networks (GAT) under physical V2X communication impairments.

  Use this skill when modifying actor-critic architectures, GAT attention mechanisms,
  reward shaping, training hyper-parameters, or running MAPPO evaluation benchmarks.
---

# MAPPO with Graph Attention Networks (GAT) Training & Evaluation Skill

This skill provides step-by-step procedures for training and evaluating cooperative neural policies under realistic V2X channel disruptions in `agents-minor`.

## Architecture Overview

1. **Decentralized Actor (`src/agents/mappo_agent.py` - `MAPPOActor`)**:
   - **Inputs**: Ego vehicle state vector ($\mathbf{x} \in \mathbb{R}^6$) and dynamic neighbor state tensor ($\mathbf{s}_j \in \mathbb{R}^{K \times 4}$).
   - **Graph Attention Layer (`src/agents/gat_layer.py`)**: Computes spatial attention coefficients $\alpha_{ij}$ across neighboring vehicles using LeakyReLU and pair-wise feature projections ($W \in \mathbb{R}^{F \times F'}$).
   - **Action Heads**:
     - Continuous Acceleration: Scaled Gaussian head $\mu_a \in [-3.0, 3.0]\,\text{m/s}^2$ with learned log-std.
     - Discrete Communication: Bernoulli logit head determining whether to broadcast state telemetry.

2. **Centralized Critic (`src/agents/mappo_agent.py` - `MAPPOCritic`)**:
   - Evaluates global multi-agent state value $V(S_{\text{global}})$ during training under the Centralized Training with Decentralized Execution (CTDE) paradigm.

3. **Reward Function**:
   $$R_i(t) = R_{\text{progress}} - \lambda_{\text{collision}} \mathbb{I}_{\text{collision}} - \lambda_{\text{comm}} \mathbb{I}_{\text{transmit}} - \lambda_{\text{jerk}} |a_t - a_{t-1}|$$
   - Penalizes collisions severely ($\lambda_{\text{collision}} = 100.0$).
   - Rewards forward velocity toward goal.
   - Applies communication thrift penalty ($\lambda_{\text{comm}} = 0.05$) to encourage selective transmission.

---

## Standard Execution & Training Workflows

### 1. Train MAPPO Policy
Executes PPO rollout collection, GAE advantage calculation, and actor-critic mini-batch updates:
```bash
.\.venv\Scripts\python.exe experiments/train_mappo.py
```
Trained weights are automatically serialized to:
- Actor Weights: `models/mappo_actor.pt`
- Critic Weights: `models/mappo_critic.pt`

### 2. Run MAPPO Evaluation Benchmark
Evaluates the trained neural policy against Rule-based, PET-Comm, and CARR baselines under extreme impairment ($L = 3, P_{\text{loss}} = 0.3, B = 2$):
```bash
.\.venv\Scripts\python.exe experiments/eval_mappo_benchmark.py
```
Metrics exported:
- Benchmark Results: `experiments/results/mappo_benchmark_results.json`
- Benchmark Plots: `experiments/results/mappo_vs_baselines.png`

---

## Key Hyperparameters

| Hyperparameter | Value | Description |
| :--- | :--- | :--- |
| `lr_actor` | $3 \times 10^{-4}$ | Adam learning rate for MAPPO actor |
| `lr_critic` | $1 \times 10^{-3}$ | Adam learning rate for centralized critic |
| `gamma` ($\gamma$) | 0.99 | Discount factor |
| `gae_lambda` ($\lambda$) | 0.95 | Generalized Advantage Estimation parameter |
| `clip_eps` ($\epsilon$) | 0.2 | PPO surrogate objective clipping threshold |
| `gat_hidden_dim` | 64 | Latent feature dimension for spatial attention |
