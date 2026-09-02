import pytest
import numpy as np
from src.estimation.kalman_filter import VehicleTrajectoryEstimator


def test_kalman_filter_prediction():
    estimator = VehicleTrajectoryEstimator(dt=0.1)
    estimator.initialize_state(pos=(0.0, 0.0), vel=(10.0, 0.0), acc=(0.0, 0.0))

    pred_x, pred_y = estimator.predict()
    # pos_x should be 0 + 10 * 0.1 = 1.0
    assert pytest.approx(pred_x, 0.01) == 1.0
    assert pytest.approx(pred_y, 0.01) == 0.0


def test_kalman_filter_update():
    estimator = VehicleTrajectoryEstimator(dt=0.1)
    estimator.initialize_state(pos=(0.0, 0.0), vel=(10.0, 0.0))

    # Predict step
    estimator.predict()

    # Update with observation matching prediction
    estimator.update(pos=(1.0, 0.0), vel=(10.0, 0.0))

    x, y = estimator.get_position()
    assert pytest.approx(x, 0.1) == 1.0
    assert pytest.approx(y, 0.1) == 0.0
