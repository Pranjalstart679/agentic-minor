import os
import sys
import json
import math
import random
import numpy as np
import torch
import matplotlib.pyplot as plt
from typing import Dict, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.env.comm_channel import CommunicationChannel
from src.env.traffic_env import TrafficEnvironment
from src.agents.rule_agent import RuleBasedCooperativeAgent
from src.agents.pet_comm_agent import PETCommAgent
from src.agents.carr_agent import CARRAgent
from src.agents.mappo_agent import MAPPOActor, MAPPOAgent


def eval_mappo_suite(num_episodes: int = 50, seed: int = 200) -> Dict[str, dict]:
    random.seed(seed)
    np.random.seed(seed)

    # Load trained MAPPO weights
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    actor_path = os.path.join(models_dir, "mappo_actor.pt")

    trained_actor = MAPPOActor()
    if os.path.exists(actor_path):
        trained_actor.load_state_dict(torch.load(actor_path))
        print("Successfully loaded MAPPO trained policy weights.")

    agent_types = {
        "Rule_Baseline": lambda vid: RuleBasedCooperativeAgent(vid),
        "CARR_Protocol": lambda vid: CARRAgent(vid),
        "PET_Comm": lambda vid: PETCommAgent(vid),
        "MAPPO_DeepRL": lambda vid: MAPPOAgent(vid, actor_net=trained_actor),
    }

    channel_config = {"latency": 2, "packet_loss_rate": 0.3, "bandwidth_limit": 2}
    results = {}

    for a_name, make_agent in agent_types.items():
        collisions_count = 0
        mean_speeds_list = []
        messages_sent_list = []

        for ep in range(num_episodes):
            comm = CommunicationChannel(
                latency=channel_config["latency"],
                packet_loss_rate=channel_config["packet_loss_rate"],
                bandwidth_limit=channel_config["bandwidth_limit"],
                enable_rayleigh_fading=True,
                seed=seed + ep,
            )
            env = TrafficEnvironment(comm_channel=comm, dt=0.1, max_steps=120)
            env.spawn_default_scenario(randomized=True)

            agents = {vid: make_agent(vid) for vid in env.vehicles.keys()}
            all_vids = list(env.vehicles.keys())
            delivered_msgs: List = []

            for step in range(1, 120):
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

        collision_rate = collisions_count / num_episodes
        results[a_name] = {
            "collision_rate": collision_rate,
            "avg_speed": float(np.mean(mean_speeds_list)),
            "avg_msgs_sent": float(np.mean(messages_sent_list)),
        }
        print(f"Policy [{a_name}]: Collision Rate = {collision_rate*100:.1f}%, Avg Msgs = {results[a_name]['avg_msgs_sent']:.1f}")

    return results


def plot_mappo_benchmark(results: Dict[str, dict], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    labels = [k.replace("_", "\n") for k in results.keys()]
    collision_rates = [v["collision_rate"] * 100 for v in results.values()]

    plt.figure(figsize=(9, 5))
    bars = plt.bar(labels, collision_rates, color=["tab:red", "tab:orange", "tab:blue", "tab:green"], alpha=0.75, width=0.45)
    plt.ylabel("Collision Rate (%) under Joint Impairment")
    plt.title("Phase 5: MAPPO Deep RL vs Heuristic Communication Policies")
    plt.ylim(0, 110)

    for bar, val in zip(bars, collision_rates):
        plt.text(bar.get_x() + bar.get_width() / 2, val + 2, f"{val:.1f}%", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "mappo_benchmark.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved MAPPO benchmark plot to {plot_path}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    res = eval_mappo_suite(num_episodes=50, seed=200)

    with open(os.path.join(out_dir, "mappo_eval_results.json"), "w") as f:
        json.dump(res, f, indent=2)

    plot_mappo_benchmark(res, out_dir)
