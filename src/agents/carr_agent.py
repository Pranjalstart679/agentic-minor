import math
from typing import Dict, List, Tuple
from src.agents.base_agent import BaseCooperativeAgent
from src.env.traffic_env import VehicleState
from src.env.comm_channel import Message, PriorityLevel


class CARRAgent(BaseCooperativeAgent):
    """
    Criticality-Aware Reliable Retransmission (CARR) Agent:
    - Normal state broadcasts use ROUTINE priority.
    - Critical emergency events (emergency braking / intersection yield) trigger CRITICAL priority messages requiring ACK.
    - Maintains unacknowledged message queue and retransmits until ACK is received or timeout occurs.
    """

    def __init__(self, vehicle_id: str, yield_ttc_threshold: float = 4.0, ack_timeout: int = 2):
        super().__init__(vehicle_id)
        self.yield_ttc_threshold = yield_ttc_threshold
        self.ack_timeout = ack_timeout

        # Pending unacknowledged critical messages: target_id -> (Message, sent_step)
        self.pending_acks: Dict[str, Tuple[Message, int]] = {}

    def compute_action(
        self,
        self_state: VehicleState,
        received_messages: List[Message],
        all_vehicle_ids: List[str],
        current_step: int,
    ) -> Tuple[float, List[Message]]:
        outgoing_msgs: List[Message] = []

        # 1. Process incoming messages & ACKs
        for msg in received_messages:
            if msg.receiver_id == self.vehicle_id:
                # Handle ACK message
                if msg.content.get("type") == "ACK":
                    acked_msg_id = msg.content.get("ack_for_id")
                    if msg.sender_id in self.pending_acks and self.pending_acks[msg.sender_id][0].msg_id == acked_msg_id:
                        del self.pending_acks[msg.sender_id]
                else:
                    self.known_neighbors[msg.sender_id] = {
                        "pos": msg.content.get("pos", (0.0, 0.0)),
                        "vel": msg.content.get("vel", (0.0, 0.0)),
                        "timestamp": msg.timestamp,
                    }
                    # Send ACK if required
                    if msg.ack_required:
                        ack_msg = Message(
                            priority=PriorityLevel.CRITICAL,
                            sender_id=self.vehicle_id,
                            receiver_id=msg.sender_id,
                            timestamp=current_step,
                            content={"type": "ACK", "ack_for_id": msg.msg_id},
                        )
                        outgoing_msgs.append(ack_msg)

        # 2. Check collision risk
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

            is_approaching = (nx * nvx + ny * nvy) < 0

            if is_approaching:
                if abs(self_ttc - n_ttc) < self.yield_ttc_threshold or n_dist < 10.0:
                    if self_dist > n_dist or (abs(self_dist - n_dist) < 0.5 and self.vehicle_id > nid):
                        should_yield = True
                        break

        if should_yield:
            action_accel = self.max_decel
            msg_priority = PriorityLevel.CRITICAL
            req_ack = True
        else:
            action_accel = self.max_accel if self_speed < self.max_speed else 0.0
            msg_priority = PriorityLevel.ROUTINE
            req_ack = False

        # 3. Retransmit unacknowledged critical messages past timeout
        for target_id, (old_msg, sent_step) in list(self.pending_acks.items()):
            if current_step - sent_step >= self.ack_timeout:
                retransmit_msg = Message(
                    priority=PriorityLevel.CRITICAL,
                    sender_id=self.vehicle_id,
                    receiver_id=target_id,
                    timestamp=current_step,
                    content={"pos": (self_state.x, self_state.y), "vel": (self_state.vx, self_state.vy), "type": "ALERT"},
                    msg_id=old_msg.msg_id,
                    ack_required=True,
                )
                outgoing_msgs.append(retransmit_msg)
                self.pending_acks[target_id] = (retransmit_msg, current_step)

        # 4. Broadcast current state
        for target_id in all_vehicle_ids:
            if target_id != self.vehicle_id and target_id not in self.pending_acks:
                msg_id = f"{self.vehicle_id}_{current_step}_{target_id}"
                msg = Message(
                    priority=msg_priority,
                    sender_id=self.vehicle_id,
                    receiver_id=target_id,
                    timestamp=current_step,
                    content={"pos": (self_state.x, self_state.y), "vel": (self_state.vx, self_state.vy)},
                    msg_id=msg_id,
                    ack_required=req_ack,
                )
                outgoing_msgs.append(msg)
                if req_ack:
                    self.pending_acks[target_id] = (msg, current_step)

        return action_accel, outgoing_msgs
