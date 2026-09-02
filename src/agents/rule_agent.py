import math
from typing import Dict, List, Tuple
from src.agents.base_agent import BaseCooperativeAgent
from src.env.traffic_env import VehicleState
from src.env.comm_channel import Message, PriorityLevel


class RuleBasedCooperativeAgent(BaseCooperativeAgent):
    """
    Baseline Cooperative Rule-Based Agent:
    - Continuously broadcasts state vector (pos, vel) to all neighbors at every step.
    - Uses received neighbor state updates to compute Time-To-Collision (TTC) towards intersection center (0,0).
    - Decelerates if another agent has priority or if TTC < threshold.
    """

    def __init__(self, vehicle_id: str, yield_ttc_threshold: float = 4.0):
        super().__init__(vehicle_id)
        self.yield_ttc_threshold = yield_ttc_threshold

    def compute_action(
        self,
        self_state: VehicleState,
        received_messages: List[Message],
        all_vehicle_ids: List[str],
        current_step: int,
    ) -> Tuple[float, List[Message]]:
        # 1. Process incoming messages to update neighbor knowledge
        for msg in received_messages:
            if msg.receiver_id in [self.vehicle_id, "broadcast"]:
                self.known_neighbors[msg.sender_id] = {
                    "pos": msg.content.get("pos", (0.0, 0.0)),
                    "vel": msg.content.get("vel", (0.0, 0.0)),
                    "timestamp": msg.timestamp,
                }

        # 2. Determine acceleration action based on self state & known neighbor states
        self_dist = math.hypot(self_state.x, self_state.y)
        self_speed = math.hypot(self_state.vx, self_state.vy)
        self_ttc = self_dist / max(0.1, self_speed)

        should_yield = False

        for nid, ndata in self.known_neighbors.items():
            if nid == self.vehicle_id:
                continue

            nx, ny = ndata["pos"]
            nvx, nvy = ndata["vel"]
            n_dist = math.hypot(nx, ny)
            n_speed = math.hypot(nvx, nvy)
            n_ttc = n_dist / max(0.1, n_speed)

            # Check if neighbor is approaching intersection center (dot product < 0)
            is_approaching = (nx * nvx + ny * nvy) < 0

            if is_approaching:
                time_diff = abs(self_ttc - n_ttc)
                if time_diff < self.yield_ttc_threshold or n_dist < 10.0:
                    if self_dist > n_dist or (abs(self_dist - n_dist) < 0.5 and self.vehicle_id > nid):
                        should_yield = True
                        break

        # If yielding, apply strong deceleration; otherwise maintain cruising speed
        if should_yield:
            action_accel = self.max_decel  # -6.0 m/s^2
        else:
            if self_speed < self.max_speed:
                action_accel = self.max_accel  # +3.0 m/s^2
            else:
                action_accel = 0.0

        # 3. Construct outgoing state broadcast messages to all neighbors
        outgoing_msgs = []
        for target_id in all_vehicle_ids:
            if target_id != self.vehicle_id:
                msg = Message(
                    priority=PriorityLevel.ROUTINE,
                    sender_id=self.vehicle_id,
                    receiver_id=target_id,
                    timestamp=current_step,
                    content={"pos": (self_state.x, self_state.y), "vel": (self_state.vx, self_state.vy)},
                )
                outgoing_msgs.append(msg)

        return action_accel, outgoing_msgs
