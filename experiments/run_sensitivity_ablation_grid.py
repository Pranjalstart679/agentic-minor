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


def run_single_simulation(
    channel: CommunicationChannel,
    agent_type: str,
    epsilon: float = 1.0,
    t_safe: int = 5,
    num_vehicles: int = 4,
    max_steps: int = 100,
) -> dict:
    env = TrafficEnvironment(comm_channel=channel, max_steps=max_steps)
    if num_vehicles == 4:
        env.spawn_default_scenario(randomized=True)
    else:
        env.spawn_scalable_intersection(num_vehicles=num_vehicles, randomized=True)

    agents = {}
    for vid in env.vehicles.keys():
        if agent_type == "pet_comm":
            agents[vid] = PETCommAgent(vid, epsilon=epsilon, t_safe=t_safe)
        elif agent_type == "carr":
            agents[vid] = CARRAgent(vid)
        else:
            agents[vid] = RuleBasedCooperativeAgent(vid)

    for step in range(max_steps):
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
        "had_collision": 1 if metrics["total_collisions"] > 0 else 0,
        "total_collisions": metrics["total_collisions"],
        "mean_speed": metrics["mean_speed"],
        "total_messages": metrics["total_messages_sent"],
        "delivery_rate": metrics["delivery_rate"],
    }


def sweep_parameter(param_name: str, values: list, num_trials: int = 20):
    results = {"baseline": [], "carr": [], "pet_comm": []}

    for val in values:
        for ag_name in ["baseline", "carr", "pet_comm"]:
            collisions = []
            speeds = []
            messages = []

            for _ in range(num_trials):
                # Configure default impaired channel
                lat = 2
                loss = 0.20
                bw = 2
                rayleigh = True
                eps = 1.0
                n_veh = 4

                if param_name == "epsilon":
                    eps = val
                elif param_name == "latency":
                    lat = int(val)
                elif param_name == "packet_loss":
                    loss = float(val)
                elif param_name == "bandwidth":
                    bw = int(val)
                elif param_name == "density":
                    n_veh = int(val)

                ch = CommunicationChannel(
                    latency=lat,
                    packet_loss_rate=loss,
                    bandwidth_limit=bw,
                    enable_rayleigh_fading=rayleigh,
                )

                res = run_single_simulation(
                    channel=ch,
                    agent_type=ag_name,
                    epsilon=eps,
                    num_vehicles=n_veh,
                    max_steps=100,
                )
                collisions.append(res["had_collision"])
                speeds.append(res["mean_speed"])
                messages.append(res["total_messages"])

            results[ag_name].append({
                "param_value": val,
                "collision_rate": float(np.mean(collisions)) * 100.0,
                "mean_speed": float(np.mean(speeds)),
                "avg_messages": float(np.mean(messages)),
            })

    return results


def run_full_sensitivity_suite():
    random.seed(42)
    np.random.seed(42)

    print("================================================================================")
    print("      RUNNING PHASE 7: SENSITIVITY & ABLATION EXPERIMENTS                      ")
    print("================================================================================")

    # 1. Epsilon threshold sweep (Pareto analysis)
    eps_vals = [0.1, 0.5, 1.0, 2.0, 3.0, 5.0]
    print("\n1. Sweeping Epsilon Threshold (PET-Comm Event Trigger)...")
    eps_results = sweep_parameter("epsilon", eps_vals, num_trials=25)

    # 2. Latency sweep
    lat_vals = [0, 1, 2, 3, 5]
    print("\n2. Sweeping Network Latency L...")
    lat_results = sweep_parameter("latency", lat_vals, num_trials=20)

    # 3. Packet loss sweep
    loss_vals = [0.0, 0.1, 0.2, 0.3, 0.4, 0.6]
    print("\n3. Sweeping Packet Loss Rate P_loss...")
    loss_results = sweep_parameter("packet_loss", loss_vals, num_trials=20)

    # 4. Bandwidth limit sweep
    bw_vals = [1, 2, 4, 8, 16]
    print("\n4. Sweeping Bandwidth Limit B...")
    bw_results = sweep_parameter("bandwidth", bw_vals, num_trials=20)

    # 5. Density scalability sweep
    density_vals = [4, 8, 12, 16, 20]
    print("\n5. Sweeping Vehicle Density Scalability N...")
    density_results = sweep_parameter("density", density_vals, num_trials=20)

    master_results = {
        "epsilon_sweep": eps_results,
        "latency_sweep": lat_results,
        "packet_loss_sweep": loss_results,
        "bandwidth_sweep": bw_results,
        "density_sweep": density_results,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "sensitivity_ablation_results.json")
    with open(json_path, "w") as f:
        json.dump(master_results, f, indent=2)
    print(f"\n[Saved JSON Sensitivity Suite]: {json_path}")

    # Generate 4-panel Sensitivity & Pareto plot
    plot_4panel_sensitivity(master_results, os.path.join(out_dir, "sensitivity_pareto_ablation.png"))

    # Generate Scalability plot
    plot_scalability(density_results, os.path.join(out_dir, "density_scalability.png"))


def plot_4panel_sensitivity(results: dict, out_png: str):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=300)

    # (a) Epsilon Pareto Curve (Collision vs Msg Overhead)
    ax_eps = axes[0, 0]
    pet_eps = results["epsilon_sweep"]["pet_comm"]
    eps_x = [r["avg_messages"] for r in pet_eps]
    eps_y = [r["collision_rate"] for r in pet_eps]
    labels = [f"ε={r['param_value']}m" for r in pet_eps]
    
    ax_eps.plot(eps_x, eps_y, color="#2e6da4", marker="o", linewidth=2.5, markersize=8)
    for i, txt in enumerate(labels):
        ax_eps.annotate(txt, (eps_x[i] + 5, eps_y[i] + 1.5), fontsize=9, fontweight="bold")
    ax_eps.set_title("(a) Pareto Frontier: Safety vs. Message Volume (ε sweep)", fontsize=11, fontweight="bold")
    ax_eps.set_xlabel("Average Transmitted Messages per Episode", fontsize=10)
    ax_eps.set_ylabel("Collision Rate (%)", fontsize=10)
    ax_eps.grid(True, linestyle="--", alpha=0.5)

    # (b) Latency Sensitivity
    ax_lat = axes[0, 1]
    for k, color, label in [("baseline", "#d9534f", "Baseline Broadcast"), ("carr", "#f0ad4e", "CARR Protocol"), ("pet_comm", "#2e6da4", "PET-Comm (Ours)")]:
        data = results["latency_sweep"][k]
        ax_lat.plot([r["param_value"] for r in data], [r["collision_rate"] for r in data], color=color, marker="o", label=label, linewidth=2.0)
    ax_lat.set_title("(b) Sensitivity to Channel Latency (L)", fontsize=11, fontweight="bold")
    ax_lat.set_xlabel("Latency L (timesteps)", fontsize=10)
    ax_lat.set_ylabel("Collision Rate (%)", fontsize=10)
    ax_lat.grid(True, linestyle="--", alpha=0.5)
    ax_lat.legend()

    # (c) Packet Loss Sensitivity
    ax_loss = axes[1, 0]
    for k, color, label in [("baseline", "#d9534f", "Baseline Broadcast"), ("carr", "#f0ad4e", "CARR Protocol"), ("pet_comm", "#2e6da4", "PET-Comm (Ours)")]:
        data = results["packet_loss_sweep"][k]
        ax_loss.plot([r["param_value"] * 100 for r in data], [r["collision_rate"] for r in data], color=color, marker="s", label=label, linewidth=2.0)
    ax_loss.set_title("(c) Sensitivity to Packet Drop Probability (P_loss)", fontsize=11, fontweight="bold")
    ax_loss.set_xlabel("Packet Loss Rate (%)", fontsize=10)
    ax_loss.set_ylabel("Collision Rate (%)", fontsize=10)
    ax_loss.grid(True, linestyle="--", alpha=0.5)

    # (d) Bandwidth Limit Sensitivity
    ax_bw = axes[1, 1]
    for k, color, label in [("baseline", "#d9534f", "Baseline Broadcast"), ("carr", "#f0ad4e", "CARR Protocol"), ("pet_comm", "#2e6da4", "PET-Comm (Ours)")]:
        data = results["bandwidth_sweep"][k]
        ax_bw.plot([r["param_value"] for r in data], [r["collision_rate"] for r in data], color=color, marker="^", label=label, linewidth=2.0)
    ax_bw.set_title("(d) Robustness under Bandwidth Limits (B)", fontsize=11, fontweight="bold")
    ax_bw.set_xlabel("Max Messages Delivered per Step (B)", fontsize=10)
    ax_bw.set_ylabel("Collision Rate (%)", fontsize=10)
    ax_bw.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()
    print(f"[Saved 4-Panel Sensitivity Plot]: {out_png}")


def plot_scalability(density_results: dict, out_png: str):
    plt.figure(figsize=(8, 5), dpi=300)
    for k, color, label, marker in [
        ("baseline", "#d9534f", "Baseline Broadcast", "s"),
        ("carr", "#f0ad4e", "CARR Protocol", "^"),
        ("pet_comm", "#2e6da4", "PET-Comm (Ours)", "o"),
    ]:
        data = density_results[k]
        plt.plot(
            [r["param_value"] for r in data],
            [r["collision_rate"] for r in data],
            color=color,
            marker=marker,
            label=label,
            linewidth=2.2,
            markersize=7,
        )
    plt.title("Multi-Agent Density Scalability under Physical Channel Bottlenecks", fontsize=12, fontweight="bold")
    plt.xlabel("Number of Interacting Vehicles (N)", fontsize=11)
    plt.ylabel("Collision Rate (%)", fontsize=11)
    plt.xticks([4, 8, 12, 16, 20])
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(out_png, bbox_inches="tight")
    plt.close()
    print(f"[Saved Scalability Plot]: {out_png}")


if __name__ == "__main__":
    run_full_sensitivity_suite()
