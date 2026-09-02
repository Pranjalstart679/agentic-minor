import pytest
from src.agents.rule_agent import RuleBasedCooperativeAgent
from src.agents.pet_comm_agent import PETCommAgent
from src.agents.carr_agent import CARRAgent
from src.env.traffic_env import VehicleState
from src.env.comm_channel import PriorityLevel


def test_rule_agent_broadcast():
    agent = RuleBasedCooperativeAgent("v_N")
    vstate = VehicleState("v_N", x=0.0, y=50.0, vx=0.0, vy=-10.0)
    acc, msgs = agent.compute_action(vstate, [], ["v_N", "v_S"], current_step=1)

    # Should attempt to accelerate towards cruising speed if no immediate conflict
    assert acc > 0.0
    # Should broadcast to neighbor v_S
    assert len(msgs) == 1
    assert msgs[0].receiver_id == "v_S"
    assert msgs[0].priority == PriorityLevel.ROUTINE


def test_pet_comm_event_triggering():
    agent = PETCommAgent("v_N", epsilon=1.0)
    vstate1 = VehicleState("v_N", x=0.0, y=50.0, vx=0.0, vy=-10.0)

    # Step 1: Always triggers broadcast
    _, msgs1 = agent.compute_action(vstate1, [], ["v_N", "v_S"], current_step=1)
    assert len(msgs1) == 1

    # Step 2: Position moved by only 0.1m (< epsilon=1.0) -> Should NOT broadcast
    vstate2 = VehicleState("v_N", x=0.0, y=49.9, vx=0.0, vy=-10.0)
    _, msgs2 = agent.compute_action(vstate2, [], ["v_N", "v_S"], current_step=2)
    assert len(msgs2) == 0


def test_carr_agent_critical_ack():
    agent = CARRAgent("v_S")
    vstate = VehicleState("v_S", x=0.0, y=-10.0, vx=0.0, vy=10.0)

    # Simulate close conflict with neighbor v_N -> Triggers CRITICAL priority with ACK required
    agent.known_neighbors["v_N"] = {"pos": (0.0, 10.0), "vel": (0.0, -10.0), "timestamp": 1}
    acc, msgs = agent.compute_action(vstate, [], ["v_N", "v_S"], current_step=2)

    assert acc < 0.0  # Decelerating to yield
    assert len(msgs) >= 1
    assert msgs[0].priority == PriorityLevel.CRITICAL
    assert msgs[0].ack_required is True
