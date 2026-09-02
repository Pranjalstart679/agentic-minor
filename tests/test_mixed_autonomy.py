import pytest
import math
from src.env.comm_channel import CommunicationChannel
from src.env.traffic_env import TrafficEnvironment, VehicleState
from src.agents.idm_human_agent import IDMHumanAgent
from src.agents.pet_comm_agent import PETCommAgent


def test_idm_human_agent_free_road():
    """Verify IDM accelerates when the road ahead is completely clear."""
    agent = IDMHumanAgent("hdv_1", v0=15.0, a_max=2.0)
    state = VehicleState("hdv_1", x=0.0, y=0.0, vx=5.0, vy=0.0, heading=0.0)
    acc, msgs = agent.compute_action(state, [], ["hdv_1"], 1)
    
    # Should accelerate towards desired speed v0 and transmit 0 messages
    assert acc > 0.5
    assert len(msgs) == 0


def test_idm_human_agent_car_following_braking():
    """Verify IDM decelerates when approaching a slower vehicle directly ahead."""
    agent = IDMHumanAgent("hdv_1", v0=15.0, s0=2.0, T=1.5)
    my_state = VehicleState("hdv_1", x=0.0, y=0.0, vx=14.0, vy=0.0, heading=0.0)
    lead_state = VehicleState("hdv_lead", x=8.0, y=0.0, vx=2.0, vy=0.0, heading=0.0)
    
    agent.update_sensor_vision({"hdv_1": my_state, "hdv_lead": lead_state})
    acc, msgs = agent.compute_action(my_state, [], ["hdv_1", "hdv_lead"], 1)
    
    # Should brake strongly to avoid collision and transmit 0 messages
    assert acc < -1.0
    assert len(msgs) == 0


def test_spawn_roundabout_scenario():
    """Verify roundabout initialization creates valid circular and approaching vehicles."""
    channel = CommunicationChannel()
    env = TrafficEnvironment(channel)
    env.spawn_roundabout_scenario(num_circulating=4, num_approaching=4, radius=25.0)
    
    assert len(env.vehicles) == 8
    assert "circ_0" in env.vehicles
    assert "app_N" in env.vehicles
    
    # Verify circulating vehicles lie near circle radius
    circ_v = env.vehicles["circ_0"]
    radius_calc = math.hypot(circ_v.x, circ_v.y)
    assert abs(radius_calc - 25.0) < 1.0


def test_spawn_scalable_intersection():
    """Verify scalable intersection initialization handles arbitrary vehicle counts."""
    channel = CommunicationChannel()
    env = TrafficEnvironment(channel)
    env.spawn_scalable_intersection(num_vehicles=12)
    
    assert len(env.vehicles) == 12
    assert "v_N_0" in env.vehicles
    assert "v_W_2" in env.vehicles


def test_mixed_autonomy_simulation_step():
    """Verify simulation runs smoothly with mixed IDM human drivers and communicative CAVs."""
    channel = CommunicationChannel(latency=1, packet_loss_rate=0.1, bandwidth_limit=4)
    env = TrafficEnvironment(channel)
    env.spawn_scalable_intersection(num_vehicles=8)
    
    agents = {}
    for idx, vid in enumerate(env.vehicles.keys()):
        if idx % 2 == 0:
            agents[vid] = PETCommAgent(vid, epsilon=1.0)
        else:
            agents[vid] = IDMHumanAgent(vid, v0=10.0)
            
    for step in range(20):
        # Update vision for IDM agents
        for vid, ag in agents.items():
            if isinstance(ag, IDMHumanAgent):
                ag.update_sensor_vision(env.vehicles)
                
        actions = {}
        all_vids = list(env.vehicles.keys())
        for vid, ag in agents.items():
            acc, msgs = ag.compute_action(env.vehicles[vid], [], all_vids, step)
            actions[vid] = acc
            for m in msgs:
                env.send_agent_message(m.sender_id, m.receiver_id, m.content, m.priority, m.ack_required)
                
        env.step(actions)
        
    metrics = env.get_metrics()
    assert metrics["total_steps"] == 20
