import numpy as np
from typing import Tuple


class VehicleTrajectoryEstimator:
    """
    2D Constant Acceleration Kalman Filter for estimating vehicle kinematics:
    State vector x = [pos_x, pos_y, vel_x, vel_y, acc_x, acc_y]^T
    """

    def __init__(self, dt: float = 0.1, process_noise_std: float = 0.1, measurement_noise_std: float = 0.5):
        self.dt = dt

        # State vector [6x1]
        self.x = np.zeros((6, 1))

        # State transition matrix F [6x6]
        self.F = np.eye(6)
        # pos_x += vel_x * dt + 0.5 * acc_x * dt^2
        self.F[0, 2] = dt
        self.F[0, 4] = 0.5 * (dt**2)
        # pos_y += vel_y * dt + 0.5 * acc_y * dt^2
        self.F[1, 3] = dt
        self.F[1, 5] = 0.5 * (dt**2)
        # vel_x += acc_x * dt
        self.F[2, 4] = dt
        # vel_y += acc_y * dt
        self.F[3, 5] = dt

        # Measurement matrix H [4x6] (observing pos_x, pos_y, vel_x, vel_y)
        self.H = np.zeros((4, 6))
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0
        self.H[2, 2] = 1.0
        self.H[3, 3] = 1.0

        # Process noise covariance Q [6x6]
        self.Q = np.eye(6) * (process_noise_std**2)

        # Measurement noise covariance R [4x4]
        self.R = np.eye(4) * (measurement_noise_std**2)

        # State covariance matrix P [6x6]
        self.P = np.eye(6) * 1.0

    def initialize_state(self, pos: Tuple[float, float], vel: Tuple[float, float], acc: Tuple[float, float] = (0.0, 0.0)):
        self.x[0, 0] = pos[0]
        self.x[1, 0] = pos[1]
        self.x[2, 0] = vel[0]
        self.x[3, 0] = vel[1]
        self.x[4, 0] = acc[0]
        self.x[5, 0] = acc[1]

    def predict(self) -> Tuple[float, float]:
        """
        Predict state forward by 1 timestep (dt).
        Returns predicted (pos_x, pos_y).
        """
        self.x = self.F @ self.x
        self.P = self.F @ self.P @ self.F.T + self.Q
        return float(self.x[0, 0]), float(self.x[1, 0])

    def update(self, pos: Tuple[float, float], vel: Tuple[float, float]):
        """
        Update state estimate with incoming measurement observation.
        """
        z = np.array([[pos[0]], [pos[1]], [vel[0]], [vel[1]]])
        y = z - self.H @ self.x  # Innovation / residual
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)  # Kalman Gain

        self.x = self.x + K @ y
        I = np.eye(6)
        self.P = (I - K @ self.H) @ self.P

    def get_position(self) -> Tuple[float, float]:
        return float(self.x[0, 0]), float(self.x[1, 0])

    def get_velocity(self) -> Tuple[float, float]:
        return float(self.x[2, 0]), float(self.x[3, 0])

    def get_full_state(self) -> np.ndarray:
        return self.x.copy()
