from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from src.env.traffic_env import VehicleState
from src.env.comm_channel import Message


class BaseCooperativeAgent(ABC):
    """
    Abstract base class for all cooperative V2X agents.
    """

    def __init__(self, vehicle_id: str, max_speed: float = 12.0, max_accel: float = 3.0, max_decel: float = -6.0):
        self.vehicle_id = vehicle_id
        self.max_speed = max_speed
        self.max_accel = max_accel
        self.max_decel = max_decel
        self.known_neighbors: Dict[str, dict] = {}

    @abstractmethod
    def compute_action(
        self,
        self_state: VehicleState,
        received_messages: List[Message],
        all_vehicle_ids: List[str],
        current_step: int,
    ) -> Tuple[float, List[Message]]:
        """
        Computes control action (acceleration delta) and list of outgoing messages to transmit.
        Returns: (acceleration_action, outgoing_messages)
        """
        pass

    def reset(self):
        self.known_neighbors.clear()
