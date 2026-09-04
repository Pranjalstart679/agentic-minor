import math
import pytest
from src.env.comm_channel import CommunicationChannel, Message, PriorityLevel
from src.env.traffic_env import TrafficEnvironment, VehicleState
from src.agents.pet_comm_agent import PETCommAgent
from src.agents.idm_human_agent import IDMHumanAgent


def test_sat_obb_collision_detection():
    """
    Tests Oriented Bounding Box collision detection using Separating Axis Theorem.
    """
    comm = CommunicationChannel()
    env = TrafficEnvironment(comm_channel=comm, safety_distance=1.0)

    # Vehicle 1 facing East at (0, 0), length 4.5, width 2.0 -> x in [-2.25, 2.25], y in [-1.0, 1.0]
    v1 = VehicleState("v1", x=0.0, y=0.0, vx=0.0, vy=0.0, heading=0.0, length=4.5, width=2.0)

    # Vehicle 2 facing North at (2.0, 0.0), length 4.5, width 2.0 -> overlaps with v1
    v2_overlapping = VehicleState("v2", x=2.0, y=0.0, vx=0.0, vy=0.0, heading=math.pi / 2, length=4.5, width=2.0)
    assert env.check_collision(v1, v2_overlapping) is True

    # Vehicle 3 at (10.0, 0.0) -> clearly separated
    v3_separated = VehicleState("v3", x=10.0, y=0.0, vx=0.0, vy=0.0, heading=0.0, length=4.5, width=2.0)
    assert env.check_collision(v1, v3_separated) is False


def test_age_of_information_tracking():
    """
    Tests that AoI increases when messages are delayed/dropped and drops upon reception.
    """
    comm = CommunicationChannel(latency=0, packet_loss_rate=0.0)
    env = TrafficEnvironment(comm_channel=comm)
    env.vehicles["v1"] = VehicleState("v1", x=0.0, y=20.0, vx=0.0, vy=-5.0, heading=-math.pi / 2)
    env.vehicles["v2"] = VehicleState("v2", x=0.0, y=-20.0, vx=0.0, vy=5.0, heading=math.pi / 2)

    # Step 1: No message sent yet -> AoI is 1
    env.step({})
    metrics1 = env.get_metrics()
    assert metrics1["mean_aoi"] >= 1.0

    # Step 2: v1 sends a message to v2
    env.send_agent_message("v1", "v2", {"pos": (0.0, 15.0)})
    env.step({})
    metrics2 = env.get_metrics()
    # Reception resets pair (v2, v1) AoI to 0 at delivery step
    assert env.last_delivery_step.get(("v2", "v1")) == 2


def test_adaptive_epsilon_tightens_near_conflict():
    """
    Tests that adaptive epsilon shrinks as vehicle approaches conflict point (0, 0).
    """
    agent = PETCommAgent("v_N", epsilon=2.0, adaptive_epsilon=True, d_conflict_max=50.0)

    # Vehicle far from conflict center (50m out)
    v_far = VehicleState("v_N", x=0.0, y=50.0, vx=0.0, vy=-8.0)
    # First step records baseline
    agent.compute_action(v_far, [], ["v_N", "v_S"], current_step=1)

    # Small displacement of 0.5m: far away, effective epsilon is approx 2.0 * (50/50) * (1/1.1) ~ 1.81m > 0.5m
    v_far_moved = VehicleState("v_N", x=0.0, y=49.5, vx=0.0, vy=-8.0)
    _, msgs_far = agent.compute_action(v_far_moved, [], ["v_N", "v_S"], current_step=2)
    # Should NOT trigger comm because 0.5m < 1.81m
    assert len(msgs_far) == 0

    # Reset agent near conflict center (10m out)
    agent_close = PETCommAgent("v_N", epsilon=2.0, adaptive_epsilon=True, d_conflict_max=50.0)
    v_close = VehicleState("v_N", x=0.0, y=10.0, vx=0.0, vy=-8.0)
    agent_close.compute_action(v_close, [], ["v_N", "v_S"], current_step=1)

    # Same 0.5m displacement: close to intersection, effective epsilon is approx 2.0 * (10/50) * (1/1.1) ~ 0.36m < 0.5m
    v_close_moved = VehicleState("v_N", x=0.0, y=9.5, vx=0.0, vy=-8.0)
    _, msgs_close = agent_close.compute_action(v_close_moved, [], ["v_N", "v_S"], current_step=2)
    # SHOULD trigger comm because 0.5m > 0.36m
    assert len(msgs_close) == 1


def test_idm_cross_traffic_yielding():
    """
    Tests that IDMHumanAgent applies braking when cross-traffic has right of way at intersection.
    """
    human_agent = IDMHumanAgent("v_N")
    # Ego vehicle v_N approaching intersection from North at y=25.0
    ego_state = VehicleState("v_N", x=0.0, y=25.0, vx=0.0, vy=-8.0, heading=-math.pi / 2)

    # Cross-traffic vehicle v_E is closer to the center (x=10.0), arriving first
    cross_vehicle = VehicleState("v_E", x=10.0, y=0.0, vx=-8.0, vy=0.0, heading=math.pi)

    human_agent.update_sensor_vision({"v_N": ego_state, "v_E": cross_vehicle})
    acc, msgs = human_agent.compute_action(ego_state, [], ["v_N", "v_E"], current_step=1)

    # Ego vehicle should decelerate (yield) to let the closer cross vehicle through
    assert acc < 0.0
    # Human drivers never transmit V2X packets
    assert len(msgs) == 0
