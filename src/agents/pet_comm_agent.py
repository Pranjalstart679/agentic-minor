import math
from typing import Dict, List, Tuple
from src.agents.base_agent import BaseCooperativeAgent
from src.env.traffic_env import VehicleState
from src.env.comm_channel import Message, PriorityLevel
from src.estimation.kalman_filter import VehicleTrajectoryEstimator


class PETCommAgent(BaseCooperativeAgent):
    """
    Predictive Event-Triggered Communication (PET-Comm) Agent:
    - Maintains Kalman Filter trajectory estimators for neighbors.
    - Triggers state broadcast only when actual position deviates > threshold epsilon from last transmitted prediction.
    - Fallback: Uses predictions under packet loss up to safety deadline T_safe timesteps, then decelerates safely.
    """

    def __init__(
        self,
        vehicle_id: str,
        epsilon: float = 1.0,  # Base deviation threshold to trigger comm (meters)
        t_safe: int = 5,       # Safety deadline under dropped packets (steps)
        yield_ttc_threshold: float = 4.0,
        adaptive_epsilon: bool = False,  # Context-aware dynamic threshold
        d_conflict_max: float = 50.0,    # Normalization distance for conflict proximity
    ):
        super().__init__(vehicle_id)
        self.epsilon = epsilon
        self.t_safe = t_safe
        self.yield_ttc_threshold = yield_ttc_threshold
        self.adaptive_epsilon = adaptive_epsilon
        self.d_conflict_max = d_conflict_max

        self.last_sent_pos: Tuple[float, float] = (0.0, 0.0)
        self.last_sent_vel: Tuple[float, float] = (0.0, 0.0)
        self.neighbor_estimators: Dict[str, VehicleTrajectoryEstimator] = {}
        self.last_updated_step: Dict[str, int] = {}

    def compute_action(
        self,
        self_state: VehicleState,
        received_messages: List[Message],
        all_vehicle_ids: List[str],
        current_step: int,
    ) -> Tuple[float, List[Message]]:
        # 1. Process incoming messages & update Kalman Filter estimators
        for msg in received_messages:
            if msg.receiver_id in [self.vehicle_id, "broadcast"]:
                sender = msg.sender_id
                pos = msg.content.get("pos", (0.0, 0.0))
                vel = msg.content.get("vel", (0.0, 0.0))

                if sender not in self.neighbor_estimators:
                    est = VehicleTrajectoryEstimator(dt=0.1)
                    est.initialize_state(pos=pos, vel=vel)
                    self.neighbor_estimators[sender] = est
                else:
                    self.neighbor_estimators[sender].update(pos=pos, vel=vel)

                self.last_updated_step[sender] = current_step

        # 2. Advance Kalman Filter predictions for stale neighbors
        should_yield = False
        self_dist = math.hypot(self_state.x, self_state.y)
        self_speed = math.hypot(self_state.vx, self_state.vy)
        self_ttc = self_dist / max(0.1, self_speed)

        for nid in all_vehicle_ids:
            if nid == self.vehicle_id:
                continue

            if nid in self.neighbor_estimators:
                estimator = self.neighbor_estimators[nid]
                pred_x, pred_y = estimator.predict()
                pred_vx, pred_vy = estimator.get_velocity()

                steps_since_update = current_step - self.last_updated_step.get(nid, 0)
                n_dist = math.hypot(pred_x, pred_y)
                n_speed = math.hypot(pred_vx, pred_vy)
                n_ttc = n_dist / max(0.1, n_speed)

                # Fallback rule: If packet loss exceeds T_safe, apply conservative yield
                if steps_since_update > self.t_safe:
                    should_yield = True
                    break

                is_approaching = (pred_x * pred_vx + pred_y * pred_vy) < 0

                if is_approaching:
                    if abs(self_ttc - n_ttc) < self.yield_ttc_threshold or n_dist < 10.0:
                        if self_dist > n_dist or (abs(self_dist - n_dist) < 0.5 and self.vehicle_id > nid):
                            should_yield = True
                            break

        if should_yield:
            action_accel = self.max_decel
        else:
            action_accel = self.max_accel if self_speed < self.max_speed else 0.0

        # 3. Check Event-Trigger Condition to decide whether to broadcast
        pos_dev = math.hypot(self_state.x - self.last_sent_pos[0], self_state.y - self.last_sent_pos[1])
        outgoing_msgs = []

        # Calculate effective epsilon: if adaptive, tighten threshold when approaching conflict zone
        if self.adaptive_epsilon:
            # Distance to intersection center (0, 0)
            d_conflict = math.hypot(self_state.x, self_state.y)
            # Scaling factor bounded in [0.2, 1.5]
            proximity_factor = max(0.2, min(1.5, d_conflict / max(1.0, self.d_conflict_max)))
            # Density adjustment based on active neighbors in communication range
            num_neighbors = len(all_vehicle_ids) - 1
            density_factor = 1.0 / (1.0 + 0.1 * max(0, num_neighbors))
            effective_epsilon = self.epsilon * proximity_factor * density_factor
        else:
            effective_epsilon = self.epsilon

        if pos_dev > effective_epsilon or current_step == 1:
            self.last_sent_pos = (self_state.x, self_state.y)
            self.last_sent_vel = (self_state.vx, self_state.vy)

            for target_id in all_vehicle_ids:
                if target_id != self.vehicle_id:
                    msg = Message(
                        priority=PriorityLevel.NORMAL,
                        sender_id=self.vehicle_id,
                        receiver_id=target_id,
                        timestamp=current_step,
                        content={"pos": (self_state.x, self_state.y), "vel": (self_state.vx, self_state.vy)},
                    )
                    outgoing_msgs.append(msg)

        return action_accel, outgoing_msgs
