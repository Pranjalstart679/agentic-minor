import math
from typing import Dict, List, Optional, Tuple
from src.agents.base_agent import BaseCooperativeAgent
from src.env.traffic_env import VehicleState
from src.env.comm_channel import Message


class IDMHumanAgent(BaseCooperativeAgent):
    """
    Intelligent Driver Model (IDM) representing human-driven vehicles (HDVs)
    that do not communicate via V2X wireless channels (transmit zero messages,
    ignore wireless packets) and rely exclusively on local line-of-sight radar/visual
    headway distance and velocity differences.
    Reference: Treiber, Hennecke, and Helbing (2000).
    """

    def __init__(
        self,
        vehicle_id: str,
        v0: float = 12.0,       # Desired velocity (m/s)
        s0: float = 2.0,        # Minimum standstill distance (m)
        T: float = 1.2,         # Safe time headway (s)
        a_max: float = 2.5,     # Maximum acceleration (m/s^2)
        b_comf: float = 2.0,    # Comfortable deceleration (m/s^2)
        delta: float = 4.0,     # Acceleration exponent
    ):
        super().__init__(vehicle_id)
        self.v0 = v0
        self.s0 = s0
        self.T = T
        self.a_max = a_max
        self.b_comf = b_comf
        self.delta = delta
        self.visible_neighbors: Dict[str, VehicleState] = {}

    def update_sensor_vision(self, all_states: Dict[str, VehicleState]):
        """
        Updates onboard visual/radar line-of-sight tracking for nearby vehicles.
        """
        self.visible_neighbors = {
            vid: state for vid, state in all_states.items() if vid != self.vehicle_id and state.active
        }

    def compute_action(
        self,
        self_state: VehicleState,
        received_messages: List[Message],
        all_vehicle_ids: List[str],
        current_step: int,
    ) -> Tuple[float, List[Message]]:
        """
        Calculates longitudinal acceleration using the IDM differential equation:
        a = a_max * [ 1 - (v / v0)^delta - (s* / s)^2 ]
        where s* = s0 + max(0, v*T + (v * delta_v) / (2 * sqrt(a_max * b_comf)))
        HDVs produce zero outgoing communication messages (returns []).
        """
        # Speed calculation
        v = math.hypot(self_state.vx, self_state.vy)

        # Identify closest leading vehicle in field of view
        lead_distance, lead_speed_diff = self._find_leading_vehicle(self_state)

        if lead_distance is None:
            # Free-road acceleration towards v0
            acc = self.a_max * (1.0 - (v / max(self.v0, 0.1)) ** self.delta)
        else:
            # Dynamic desired headway distance s*
            s_star = self.s0 + max(
                0.0,
                v * self.T + (v * lead_speed_diff) / (2.0 * math.sqrt(max(self.a_max * self.b_comf, 0.01)))
            )
            # Full IDM acceleration
            ratio_v = (v / max(self.v0, 0.1)) ** self.delta
            ratio_s = (s_star / max(lead_distance, 0.5)) ** 2
            acc = self.a_max * (1.0 - ratio_v - ratio_s)

        # Realistic physical bounds [-6.0, 3.0] m/s^2
        clipped_acc = max(min(acc, self.max_accel), self.max_decel)
        return clipped_acc, []

    def _find_leading_vehicle(self, self_state: VehicleState) -> Tuple[Optional[float], float]:
        """
        Finds the nearest leading vehicle ahead within the field of view cone.
        Returns: (headway distance in meters, relative velocity difference in m/s).
        """
        closest_dist = None
        closest_speed_diff = 0.0

        for vid, other in self.visible_neighbors.items():
            if not other.active:
                continue

            dx = other.x - self_state.x
            dy = other.y - self_state.y
            dist = math.hypot(dx, dy)

            if dist > 60.0 or dist < 0.1:
                continue

            # Project displacement onto heading coordinate frame
            cos_h = math.cos(self_state.heading)
            sin_h = math.sin(self_state.heading)
            longitudinal_proj = dx * cos_h + dy * sin_h
            lateral_proj = -dx * sin_h + dy * cos_h

            # Vehicle is in front and within path corridor (+- 3.0m)
            if longitudinal_proj > 0 and abs(lateral_proj) < 3.0:
                if closest_dist is None or longitudinal_proj < closest_dist:
                    closest_dist = longitudinal_proj
                    other_v = math.hypot(other.vx, other.vy)
                    my_v = math.hypot(self_state.vx, self_state.vy)
                    closest_speed_diff = my_v - other_v

        return closest_dist, closest_speed_diff
