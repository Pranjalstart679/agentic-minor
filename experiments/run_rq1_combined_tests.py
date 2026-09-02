import os
import sys
import json
import math
import random
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib.pyplot as plt
from typing import Dict, List
from src.env.comm_channel import CommunicationChannel
from src.env.traffic_env import TrafficEnvironment
from src.agents.rule_agent import RuleBasedCooperativeAgent


def run_experiment_suite(num_episodes: int = 20, seed: int = 42) -> Dict[str, dict]:
    random.seed(seed)
    np.random.seed(seed)

    scenarios = {
        "1_Ideal": {"latency": 0, "packet_loss_rate": 0.0, "bandwidth_limit": None},
        "2_Latency_Only": {"latency": 2, "packet_loss_rate": 0.0, "bandwidth_limit": None},
        "3_Loss_Only": {"latency": 0, "packet_loss_rate": 0.3, "bandwidth_limit": None},
        "4_Bandwidth_Only": {"latency": 0, "packet_loss_rate": 0.0, "bandwidth_limit": 2},
        "5_Combined_Joint": {"latency": 2, "packet_loss_rate": 0.3, "bandwidth_limit": 2},
    }

    results = {}

    for s_name, s_cfg in scenarios.items():
        collisions_count = 0
        total_steps_list = []
        mean_speeds_list = []
        messages_sent_list = []
        messages_delivered_list = []

        for ep in range(num_episodes):
            comm = CommunicationChannel(
                latency=s_cfg["latency"],
                packet_loss_rate=s_cfg["packet_loss_rate"],
                bandwidth_limit=s_cfg["bandwidth_limit"],
                seed=seed + ep,
            )
            env = TrafficEnvironment(comm_channel=comm, dt=0.1, max_steps=150)
            env.spawn_default_scenario()

            # Instantiate rule-based agents
            agents = {vid: RuleBasedCooperativeAgent(vid) for vid in env.vehicles.keys()}
            all_vids = list(env.vehicles.keys())

            delivered_msgs: List = []

            for step in range(1, 150):
                actions = {}
                outgoing_all = []

                for vid, agent in agents.items():
                    vstate = env.vehicles[vid]
                    if not vstate.active:
                        continue
                    # Filter delivered messages for this agent
                    agent_msgs = [m for m in delivered_msgs if m.receiver_id in [vid, "broadcast"]]
                    acc, msgs = agent.compute_action(vstate, agent_msgs, all_vids, step)
                    actions[vid] = acc
                    outgoing_all.extend(msgs)

                # Send outgoing messages to channel
                for msg in outgoing_all:
                    env.send_agent_message(
                        sender_id=msg.sender_id,
                        receiver_id=msg.receiver_id,
                        content=msg.content,
                        priority=msg.priority,
                        ack_required=msg.ack_required,
                    )

                vstates, delivered_msgs, new_collisions = env.step(actions)

                if new_collisions:
                    collisions_count += 1
                    break

            metrics = env.get_metrics()
            total_steps_list.append(metrics["total_steps"])
            mean_speeds_list.append(metrics["mean_speed"])
            messages_sent_list.append(metrics["total_messages_sent"])
            messages_delivered_list.append(metrics["total_messages_delivered"])

        collision_rate = collisions_count / num_episodes
        results[s_name] = {
            "collision_rate": collision_rate,
            "avg_steps": float(np.mean(total_steps_list)),
            "avg_speed": float(np.mean(mean_speeds_list)),
            "avg_msgs_sent": float(np.mean(messages_sent_list)),
            "avg_msgs_delivered": float(np.mean(messages_delivered_list)),
        }
        print(f"Scenario [{s_name}]: Collision Rate = {collision_rate:.2f}, Avg Speed = {results[s_name]['avg_speed']:.2f}")

    return results


def plot_results(results: Dict[str, dict], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    labels = [k.replace("_", " ") for k in results.keys()]
    collision_rates = [v["collision_rate"] * 100 for v in results.values()]
    avg_speeds = [v["avg_speed"] for v in results.values()]

    fig, ax1 = plt.subplots(figsize=(10, 5))

    color = "tab:red"
    ax1.set_xlabel("Communication Scenario")
    ax1.set_ylabel("Collision Rate (%)", color=color)
    bars = ax1.bar(labels, collision_rates, color=color, alpha=0.6, width=0.4, align="center")
    ax1.tick_params(axis="y", labelcolor=color)
    ax1.set_ylim(0, 100)

    # Annotate bars
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(
            f"{height:.1f}%",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
        )

    plt.title("RQ1: Isolated vs. Combined Network Impairment Degradation")
    plt.xticks(rotation=15)
    plt.tight_layout()

    plot_path = os.path.join(output_dir, "rq1_impairment_degradation.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    res = run_experiment_suite(num_episodes=20, seed=42)

    with open(os.path.join(out_dir, "rq1_results.json"), "w") as f:
        json.dump(res, f, indent=2)

    plot_results(res, out_dir)
