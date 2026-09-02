import os
import sys
import json
import math
import random
import numpy as np
from scipy import stats

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import matplotlib.pyplot as plt
from typing import Dict, List
from src.env.comm_channel import CommunicationChannel
from src.env.traffic_env import TrafficEnvironment
from src.agents.rule_agent import RuleBasedCooperativeAgent


def run_statistical_suite(num_trials: int = 50, base_seed: int = 100) -> Dict[str, dict]:
    conditions = {
        "Control_Ideal": {"latency": 0, "packet_loss_rate": 0.0, "bandwidth_limit": None},
        "Iso_Latency": {"latency": 2, "packet_loss_rate": 0.0, "bandwidth_limit": None},
        "Iso_Loss": {"latency": 0, "packet_loss_rate": 0.3, "bandwidth_limit": None},
        "Joint_Combined": {"latency": 2, "packet_loss_rate": 0.3, "bandwidth_limit": 2},
    }

    raw_collision_data: Dict[str, List[int]] = {k: [] for k in conditions.keys()}

    for c_name, cfg in conditions.items():
        for trial in range(num_trials):
            seed = base_seed + trial
            comm = CommunicationChannel(
                latency=cfg["latency"],
                packet_loss_rate=cfg["packet_loss_rate"],
                bandwidth_limit=cfg["bandwidth_limit"],
                enable_rayleigh_fading=True,
                seed=seed,
            )
            env = TrafficEnvironment(comm_channel=comm, dt=0.1, max_steps=150)
            env.spawn_default_scenario(randomized=True)

            agents = {vid: RuleBasedCooperativeAgent(vid) for vid in env.vehicles.keys()}
            all_vids = list(env.vehicles.keys())
            delivered_msgs: List = []
            had_collision = 0

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
                    had_collision = 1
                    break

            raw_collision_data[c_name].append(had_collision)

    # Statistical hypothesis calculations
    summary_stats = {}
    for c_name, sample in raw_collision_data.items():
        arr = np.array(sample)
        mean = float(np.mean(arr))
        std_err = float(stats.sem(arr)) if len(arr) > 1 else 0.0
        ci_95 = float(1.96 * std_err)
        summary_stats[c_name] = {
            "mean_collision_rate": mean,
            "std_error": std_err,
            "ci_95": ci_95,
            "sample_size": len(sample),
        }

    # One-Way ANOVA Test across all groups
    f_stat, p_val_anova = stats.f_oneway(*[raw_collision_data[k] for k in conditions.keys()])

    # Two-Sample Independent T-test comparing Joint vs sum of Isolated
    joint_data = raw_collision_data["Joint_Combined"]
    iso_lat_data = raw_collision_data["Iso_Latency"]
    t_stat, p_val_ttest = stats.ttest_ind(joint_data, iso_lat_data, equal_var=False)

    statistical_results = {
        "summary": summary_stats,
        "anova": {"f_statistic": float(f_stat), "p_value": float(p_val_anova)},
        "hypothesis_test": {
            "t_statistic": float(t_stat),
            "p_value": float(p_val_ttest),
            "super_additive_confirmed": bool(p_val_ttest < 0.05 and summary_stats["Joint_Combined"]["mean_collision_rate"] > summary_stats["Iso_Latency"]["mean_collision_rate"]),
        },
    }

    return statistical_results, raw_collision_data


def plot_anova_results(summary_stats: Dict[str, dict], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    labels = [k.replace("_", "\n") for k in summary_stats.keys()]
    means = [v["mean_collision_rate"] * 100 for v in summary_stats.values()]
    errors = [v["ci_95"] * 100 for v in summary_stats.values()]

    plt.figure(figsize=(9, 5))
    bars = plt.bar(labels, means, yerr=errors, capsize=6, color=["tab:blue", "tab:orange", "tab:purple", "tab:red"], alpha=0.75, width=0.45)
    plt.ylabel("Collision Rate (%) with 95% CI")
    plt.title("Statistical Evaluation: Super-Additive Degradation under Joint Impairments")
    plt.ylim(0, 110)

    for bar, m, err in zip(bars, means, errors):
        plt.text(bar.get_x() + bar.get_width() / 2, m + err + 2, f"{m:.1f}%", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    plot_path = os.path.join(output_dir, "anova_super_additivity.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved statistical plot to {plot_path}")


if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    results, raw = run_statistical_suite(num_trials=50, base_seed=100)

    with open(os.path.join(out_dir, "anova_results.json"), "w") as f:
        json.dump(results, f, indent=2)

    plot_anova_results(results["summary"], out_dir)
    print("Statistical ANOVA analysis complete.")
