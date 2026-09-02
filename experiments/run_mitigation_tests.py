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
from src.agents.pet_comm_agent import PETCommAgent
from src.agents.carr_agent import CARRAgent


def run_mitigation_experiments(num_episodes: int = 20, seed: int = 42) -> Dict[str, dict]:
    random.seed(seed)
    np.random.seed(seed)

    agent_types = {
        "Rule_Baseline": RuleBasedCooperativeAgent,
        "PET_Comm": PETCommAgent,
        "CARR_Protocol": CARRAgent,
    }

    # Severe combined impairment configuration
    channel_config = {"latency": 2, "packet_loss_rate": 0.3, "bandwidth_limit": 2}

    results = {}

    for a_name, AgentClass in agent_types.items():
        collisions_count = 0
        mean_speeds_list = []
        messages_sent_list = []
        messages_delivered_list = []

        for ep in range(num_episodes):
            comm = CommunicationChannel(
                latency=channel_config["latency"],
                packet_loss_rate=channel_config["packet_loss_rate"],
                bandwidth_limit=channel_config["bandwidth_limit"],
                seed=seed + ep,
            )
            env = TrafficEnvironment(comm_channel=comm, dt=0.1, max_steps=150)
            env.spawn_default_scenario()

            agents = {vid: AgentClass(vid) for vid in env.vehicles.keys()}
            all_vids = list(env.vehicles.keys())

            delivered_msgs: List = []

            for step in range(1, 150):
                actions = {}
                outgoing_all = []

                for vid, agent in agents.items():
                    vstate = env.vehicles[vid]
                    if not vstate.active:
                        continue
                    agent_msgs = [m for m in delivered_msgs if m.receiver_id in [vid, "broadcast"]]
                    acc, msgs = agent.compute_action(vstate, agent_msgs, all_vids, step)
                    actions[vid] = acc
                    outgoing_all.extend(msgs)

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
            mean_speeds_list.append(metrics["mean_speed"])
            messages_sent_list.append(metrics["total_messages_sent"])
            messages_delivered_list.append(metrics["total_messages_delivered"])

        collision_rate = collisions_count / num_episodes
        results[a_name] = {
            "collision_rate": collision_rate,
            "avg_speed": float(np.mean(mean_speeds_list)),
            "avg_msgs_sent": float(np.mean(messages_sent_list)),
            "avg_msgs_delivered": float(np.mean(messages_delivered_list)),
        }
        print(
            f"Agent [{a_name}]: Collision Rate = {collision_rate:.2f}, Avg Msgs Sent = {results[a_name]['avg_msgs_sent']:.1f}"
        )

    return results


def plot_mitigation_results(results: Dict[str, dict], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    labels = list(results.keys())
    collision_rates = [v["collision_rate"] * 100 for v in results.values()]
    msgs_sent = [v["avg_msgs_sent"] for v in results.values()]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Plot 1: Collision Rate Reduction
    ax1.bar(labels, collision_rates, color="tab:blue", alpha=0.7)
    ax1.set_ylabel("Collision Rate (%)")
    ax1.set_title("Safety Performance under Combined Impairment")
    ax1.set_ylim(0, 100)
    for i, v in enumerate(collision_rates):
        ax1.text(i, v + 2, f"{v:.1f}%", ha="center")

    # Plot 2: Communication Load Reduction
    ax2.bar(labels, msgs_sent, color="tab:green", alpha=0.7)
    ax2.set_ylabel("Average Messages Sent per Episode")
    ax2.set_title("Communication Overhead / Bandwidth Efficiency")
    for i, v in enumerate(msgs_sent):
        ax2.text(i, v + 5, f"{v:.1f}", ha="center")

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "mitigation_performance.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved plot to {plot_path}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    res = run_mitigation_experiments(num_episodes=20, seed=42)

    with open(os.path.join(out_dir, "mitigation_results.json"), "w") as f:
        json.dump(res, f, indent=2)

    plot_mitigation_results(res, out_dir)
