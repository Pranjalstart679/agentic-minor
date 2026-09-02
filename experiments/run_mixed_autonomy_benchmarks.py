import os
import sys
import json
import random
import numpy as np
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.env.comm_channel import CommunicationChannel
from src.env.traffic_env import TrafficEnvironment
from src.agents.rule_agent import RuleBasedCooperativeAgent
from src.agents.pet_comm_agent import PETCommAgent
from src.agents.carr_agent import CARRAgent
from src.agents.idm_human_agent import IDMHumanAgent


def simulate_mixed_autonomy_trial(
    scenario_type: str,
    cav_agent_class,
    cav_penetration: float,
    num_vehicles: int = 8,
    max_steps: int = 100,
    latency: int = 2,
    packet_loss_rate: float = 0.20,
    bandwidth_limit: int = 2,
    enable_rayleigh_fading: bool = True,
) -> dict:
    channel = CommunicationChannel(
        latency=latency,
        packet_loss_rate=packet_loss_rate,
        bandwidth_limit=bandwidth_limit,
        enable_rayleigh_fading=enable_rayleigh_fading,
    )
    env = TrafficEnvironment(comm_channel=channel, max_steps=max_steps)

    if scenario_type == "intersection":
        env.spawn_scalable_intersection(num_vehicles=num_vehicles, randomized=True)
    elif scenario_type == "highway_merge":
        env.spawn_highway_merge_scenario(num_mainline=num_vehicles // 2, num_ramps=num_vehicles // 2)
    elif scenario_type == "roundabout":
        env.spawn_roundabout_scenario(num_circulating=num_vehicles // 2, num_approaching=num_vehicles // 2)
    else:
        env.spawn_default_scenario(randomized=True)

    vids = list(env.vehicles.keys())
    num_cavs = int(round(len(vids) * cav_penetration))
    
    # Deterministic or randomized allocation
    cav_ids = set(vids[:num_cavs])

    agents = {}
    for vid in vids:
        if vid in cav_ids:
            if cav_agent_class == PETCommAgent:
                agents[vid] = PETCommAgent(vid, epsilon=1.0, t_safe=5)
            elif cav_agent_class == CARRAgent:
                agents[vid] = CARRAgent(vid)
            else:
                agents[vid] = RuleBasedCooperativeAgent(vid)
        else:
            agents[vid] = IDMHumanAgent(vid, v0=10.0)

    for step in range(max_steps):
        # Update vision for IDM agents
        for vid, ag in agents.items():
            if isinstance(ag, IDMHumanAgent):
                ag.update_sensor_vision(env.vehicles)

        actions = {}
        all_vids = list(env.vehicles.keys())
        for vid, ag in agents.items():
            if not env.vehicles[vid].active:
                continue
            acc, msgs = ag.compute_action(env.vehicles[vid], [], all_vids, step)
            actions[vid] = acc
            for m in msgs:
                env.send_agent_message(m.sender_id, m.receiver_id, m.content, m.priority, m.ack_required)

        env.step(actions)

    metrics = env.get_metrics()
    return {
        "scenario": scenario_type,
        "cav_penetration": cav_penetration,
        "had_collision": 1 if metrics["total_collisions"] > 0 else 0,
        "total_collisions": metrics["total_collisions"],
        "mean_speed": metrics["mean_speed"],
        "total_messages": metrics["total_messages_sent"],
        "delivery_rate": metrics["delivery_rate"],
    }


def run_all_mixed_autonomy_benchmarks(num_trials_per_config: int = 15):
    random.seed(42)
    np.random.seed(42)

    scenarios = ["intersection", "highway_merge", "roundabout"]
    penetrations = [0.0, 0.25, 0.50, 0.75, 1.0]
    agent_configs = [
        ("Baseline Broadcast", RuleBasedCooperativeAgent),
        ("CARR Protocol", CARRAgent),
        ("PET-Comm (Ours)", PETCommAgent),
    ]

    all_results = {}

    print("================================================================================")
    print("      RUNNING PHASE 6: MIXED AUTONOMY & MULTI-SCENARIO BENCHMARKS              ")
    print("================================================================================")

    for sc in scenarios:
        all_results[sc] = {}
        print(f"\nEvaluating Scenario: {sc.upper()}")
        for name, ag_cls in agent_configs:
            all_results[sc][name] = []
            for p in penetrations:
                collision_counts = []
                mean_speeds = []
                msg_counts = []
                for _ in range(num_trials_per_config):
                    res = simulate_mixed_autonomy_trial(
                        scenario_type=sc,
                        cav_agent_class=ag_cls,
                        cav_penetration=p,
                        num_vehicles=8,
                        max_steps=100,
                    )
                    collision_counts.append(res["had_collision"])
                    mean_speeds.append(res["mean_speed"])
                    msg_counts.append(res["total_messages"])

                col_rate = float(np.mean(collision_counts)) * 100.0
                avg_speed = float(np.mean(mean_speeds))
                avg_msgs = float(np.mean(msg_counts))

                all_results[sc][name].append({
                    "penetration": p,
                    "collision_rate": col_rate,
                    "mean_speed": avg_speed,
                    "avg_messages": avg_msgs,
                })
                print(f"  [{sc:14s}] [{name:20s}] CAV Penetration: {int(p*100):3d}% -> Collision Rate: {col_rate:5.1f}%, Mean Speed: {avg_speed:4.2f} m/s, Msgs: {avg_msgs:5.1f}")

    # Save JSON results
    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "mixed_autonomy_results.json")
    with open(json_path, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[Saved JSON Benchmark]: {json_path}")

    # Generate Publication-Ready Plot
    generate_mixed_autonomy_plot(all_results, os.path.join(out_dir, "mixed_autonomy_benchmark.png"))


def generate_mixed_autonomy_plot(results: dict, out_png: str):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5), dpi=300)
    scenarios = ["intersection", "highway_merge", "roundabout"]
    scenario_titles = {
        "intersection": "4-Way Unsignalized Intersection",
        "highway_merge": "High-Speed Highway Merging",
        "roundabout": "Multi-Lane Urban Roundabout",
    }
    colors = {
        "Baseline Broadcast": "#d9534f",
        "CARR Protocol": "#f0ad4e",
        "PET-Comm (Ours)": "#2e6da4",
    }
    markers = {
        "Baseline Broadcast": "s",
        "CARR Protocol": "^",
        "PET-Comm (Ours)": "o",
    }

    for idx, sc in enumerate(scenarios):
        ax = axes[idx]
        sc_data = results[sc]

        for name, records in sc_data.items():
            x = [r["penetration"] * 100 for r in records]
            y = [r["collision_rate"] for r in records]
            ax.plot(
                x, y,
                label=name,
                color=colors.get(name, "black"),
                marker=markers.get(name, "o"),
                linewidth=2.2,
                markersize=7,
            )

        ax.set_title(scenario_titles[sc], fontsize=13, fontweight="bold", pad=10)
        ax.set_xlabel("CAV Penetration Rate (%)", fontsize=11)
        if idx == 0:
            ax.set_ylabel("Collision Rate (%)", fontsize=11)
        ax.set_ylim(-5, 105)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.grid(True, linestyle="--", alpha=0.5)
        if idx == 0:
            ax.legend(loc="upper right", framealpha=0.9)

    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()
    print(f"[Saved Publication Plot]: {out_png}")


if __name__ == "__main__":
    run_all_mixed_autonomy_benchmarks(num_trials_per_config=15)
