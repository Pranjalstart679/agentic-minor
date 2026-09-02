import os
import sys
import math
import random
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.env.comm_channel import CommunicationChannel
from src.env.traffic_env import TrafficEnvironment
from src.agents.mappo_agent import MAPPOActor, MAPPOCritic


def train_mappo(num_epochs: int = 50, gamma: float = 0.95, lr: float = 3e-4, seed: int = 42):
    """
    Robust Multi-Agent PPO Training Loop with Policy Gradients, Critic MSE, and Entropy Regularization.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    actor = MAPPOActor()
    critic = MAPPOCritic(global_state_dim=24)

    actor_optimizer = optim.Adam(actor.parameters(), lr=lr)
    critic_optimizer = optim.Adam(critic.parameters(), lr=lr)

    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)

    print("Starting Authentic MAPPO Deep RL Training with PPO Policy Gradients...")

    for epoch in range(1, num_epochs + 1):
        comm = CommunicationChannel(latency=2, packet_loss_rate=0.3, bandwidth_limit=2, enable_rayleigh_fading=True, seed=seed + epoch)
        env = TrafficEnvironment(comm_channel=comm, dt=0.1, max_steps=100)
        env.spawn_default_scenario(randomized=True)

        all_vids = list(env.vehicles.keys())
        delivered_msgs = []

        # Buffer for rollout trajectories
        states_buf = []
        neighbors_buf = []
        actions_buf = []
        log_probs_buf = []
        rewards_buf = []
        values_buf = []
        global_states_buf = []

        for step in range(1, 100):
            actions = {}
            step_ego_states = []
            step_neighbor_states = []
            step_actions = []
            step_log_probs = []

            # Global state vector: concat positions & velocities of 4 vehicles (4 * 6 = 24 dim)
            global_state_list = []
            for vid in all_vids:
                vs = env.vehicles[vid]
                global_state_list.extend([vs.x, vs.y, vs.vx, vs.vy, vs.ax, vs.ay])
            global_tensor = torch.tensor([global_state_list], dtype=torch.float32)
            value_est = critic(global_tensor)

            for vid in all_vids:
                vstate = env.vehicles[vid]
                if not vstate.active:
                    continue

                ego_tensor = torch.tensor([[vstate.x, vstate.y, vstate.vx, vstate.vy, vstate.ax, vstate.ay]], dtype=torch.float32)

                # Collect relative neighbor observations
                neighbor_list = []
                for other_id in all_vids:
                    if other_id != vid:
                        ov = env.vehicles[other_id]
                        neighbor_list.append([ov.x - vstate.x, ov.y - vstate.y, ov.vx - vstate.vx, ov.vy - vstate.vy])
                neighbor_tensor = torch.tensor([neighbor_list], dtype=torch.float32)

                mean, std, comm_logit = actor(ego_tensor, neighbor_tensor)
                dist = torch.distributions.Normal(mean, std)
                acc_sample = dist.sample()
                acc_clamped = torch.clamp(acc_sample, -6.0, 3.0)
                log_prob = dist.log_prob(acc_sample)

                actions[vid] = float(acc_clamped.item())
                step_ego_states.append(ego_tensor)
                step_neighbor_states.append(neighbor_tensor)
                step_actions.append(acc_clamped)
                step_log_probs.append(log_prob)

            vstates, delivered_msgs, new_collisions = env.step(actions)

            # Compute cooperative team reward
            step_reward = 0.0
            for vid, v in vstates.items():
                if v.active:
                    step_reward += 0.05 * math.hypot(v.vx, v.vy)

            if new_collisions:
                step_reward -= 50.0

            states_buf.append(step_ego_states)
            neighbors_buf.append(step_neighbor_states)
            actions_buf.append(step_actions)
            log_probs_buf.append(step_log_probs)
            rewards_buf.append(step_reward)
            values_buf.append(value_est)
            global_states_buf.append(global_tensor)

            if new_collisions:
                break

        # Compute Discounted Returns & Advantages
        T = len(rewards_buf)
        returns = []
        discounted_sum = 0.0
        for t in reversed(range(T)):
            discounted_sum = rewards_buf[t] + gamma * discounted_sum
            returns.insert(0, discounted_sum)

        returns_tensor = torch.tensor(returns, dtype=torch.float32).unsqueeze(1)
        values_tensor = torch.cat(values_buf, dim=0)
        advantages = returns_tensor - values_tensor.detach()

        # Update Critic Network (Value Loss)
        critic_loss = F.mse_loss(values_tensor, returns_tensor)
        critic_optimizer.zero_grad()
        critic_loss.backward()
        critic_optimizer.step()

        # Update Actor Network (Policy Gradient Loss)
        actor_losses = []
        for t in range(T):
            step_adv = advantages[t].item()
            for i in range(len(actions_buf[t])):
                ego_t = states_buf[t][i]
                neigh_t = neighbors_buf[t][i]
                act_t = actions_buf[t][i]
                old_log_p = log_probs_buf[t][i].detach()

                mean, std, _ = actor(ego_t, neigh_t)
                dist = torch.distributions.Normal(mean, std)
                new_log_p = dist.log_prob(act_t)
                ratio = torch.exp(new_log_p - old_log_p)

                surr1 = ratio * step_adv
                surr2 = torch.clamp(ratio, 0.8, 1.2) * step_adv
                actor_loss = -torch.min(surr1, surr2) - 0.01 * dist.entropy().mean()
                actor_losses.append(actor_loss)

        if actor_losses:
            total_actor_loss = torch.stack(actor_losses).mean()
            actor_optimizer.zero_grad()
            total_actor_loss.backward()
            actor_optimizer.step()

        if epoch % 10 == 0 or epoch == 1:
            total_ep_reward = sum(rewards_buf)
            print(f"Epoch [{epoch}/{num_epochs}]: Reward = {total_ep_reward:.2f}, Critic Loss = {critic_loss.item():.4f}")

    actor_path = os.path.join(models_dir, "mappo_actor.pt")
    torch.save(actor.state_dict(), actor_path)
    print(f"MAPPO Actor Policy successfully trained and saved to {actor_path}")


if __name__ == "__main__":
    train_mappo(num_epochs=50)
