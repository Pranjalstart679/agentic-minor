"""
SUMO Benchmark Runner and FCD Exporter.

Executes cooperative multi-agent simulations under varying V2X communication impairments
and generates SUMO network definitions and Floating Car Data (FCD) trajectory exports.
"""

import os
import sys
import json
import argparse

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.env.comm_channel import CommunicationChannel, PriorityLevel
from src.env.sumo_bridge import SumoNetworkGenerator, SumoTrafficBridge
from src.agents.rule_agent import RuleBasedCooperativeAgent
from src.agents.pet_comm_agent import PETCommAgent
from src.agents.carr_agent import CARRAgent


def run_sumo_simulation(agent_type: str = "pet_comm", packet_loss: float = 0.3, latency: int = 2, max_steps: int = 150):
    output_dir = os.path.join(os.path.dirname(__file__), "results", "sumo")
    os.makedirs(output_dir, exist_ok=True)

    # 1. Generate SUMO XML network files
    files = SumoNetworkGenerator.create_intersection_scenario(output_dir)
    print(f"[SUMO] Generated network configs in: {output_dir}")

    # 2. Setup communication channel and bridge
    channel = CommunicationChannel(
        latency=latency,
        packet_loss_rate=packet_loss,
        bandwidth_limit=8,
        enable_rayleigh_fading=True,
    )
    bridge = SumoTrafficBridge(comm_channel=channel, dt=0.1)
    bridge.initialize_scenario()

    # 3. Instantiate agents
    agent_map = {}
    vehicle_ids = list(bridge.vehicles.keys())
    for vid in vehicle_ids:
        if agent_type == "pet_comm":
            agent_map[vid] = PETCommAgent(vid, epsilon=1.0)
        elif agent_type == "carr":
            agent_map[vid] = CARRAgent(vid)
        else:
            agent_map[vid] = RuleBasedCooperativeAgent(vid)

    print(f"[SUMO] Simulating {agent_type.upper()} with Latency={latency}, Loss={packet_loss*100:.0f}%...")

    # 4. Simulation loop
    total_messages_sent = 0
    total_messages_delivered = 0
    delivered_msgs: List = []

    for step in range(1, max_steps + 1):
        accelerations = {}
        outbound_messages = []

        # Each active vehicle computes action and sends broadcast
        for vid, vstate in bridge.vehicles.items():
            if not vstate.active:
                continue
            agent = agent_map[vid]
            agent_msgs = [m for m in delivered_msgs if m.receiver_id in [vid, "broadcast"]]
            acc, msgs = agent.compute_action(
                self_state=vstate,
                received_messages=agent_msgs,
                all_vehicle_ids=vehicle_ids,
                current_step=step,
            )
            accelerations[vid] = acc
            for m in msgs:
                channel.send(m)
                outbound_messages.append(m)

        total_messages_sent += len(outbound_messages)

        # Step bridge physics and communication
        _, _, delivered_msgs = bridge.step(accelerations)
        total_messages_delivered += len(delivered_msgs)

        # Terminate early if all vehicles have crossed
        if not any(v.active for v in bridge.vehicles.values()):
            break

    # 5. Export FCD XML for SUMO visualization
    fcd_path = os.path.join(output_dir, f"trace_{agent_type}_L{latency}_loss{int(packet_loss*100)}.fcd.xml")
    bridge.export_fcd_xml(fcd_path)

    summary = {
        "agent_type": agent_type,
        "latency": latency,
        "packet_loss_rate": packet_loss,
        "steps_simulated": bridge.step_count,
        "collisions_count": len(bridge.collisions),
        "total_messages_sent": total_messages_sent,
        "total_messages_delivered": total_messages_delivered,
        "fcd_export_file": fcd_path,
    }

    summary_path = os.path.join(output_dir, f"summary_{agent_type}.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[SUMO] Finished in {bridge.step_count} steps. Collisions: {len(bridge.collisions)}")
    print(f"[SUMO] Saved Floating Car Data (FCD) trace -> {fcd_path}")
    return summary


def main():
    parser = argparse.ArgumentParser(description="Run SUMO Multi-Agent Cooperative Traffic Simulation")
    parser.add_argument("--agent", type=str, default="pet_comm", choices=["rule", "pet_comm", "carr"], help="Agent algorithm")
    parser.add_argument("--loss", type=float, default=0.2, help="Packet loss rate [0.0 - 1.0]")
    parser.add_argument("--latency", type=int, default=1, help="Latency steps")
    args = parser.parse_args()

    run_sumo_simulation(agent_type=args.agent, packet_loss=args.loss, latency=args.latency)


if __name__ == "__main__":
    main()
