import pytest
from src.env.comm_channel import CommunicationChannel, Message, PriorityLevel


def test_channel_ideal():
    channel = CommunicationChannel(latency=0, packet_loss_rate=0.0, bandwidth_limit=None)
    msg = Message(
        priority=PriorityLevel.NORMAL,
        sender_id="vehicle_1",
        receiver_id="vehicle_2",
        timestamp=0,
        content={"pos": [0, 0]},
    )
    channel.send(msg)
    delivered = channel.step()
    assert len(delivered) == 1
    assert delivered[0].sender_id == "vehicle_1"


def test_channel_latency():
    channel = CommunicationChannel(latency=2, packet_loss_rate=0.0, bandwidth_limit=None)
    msg = Message(
        priority=PriorityLevel.NORMAL,
        sender_id="vehicle_1",
        receiver_id="vehicle_2",
        timestamp=0,
        content={"pos": [0, 0]},
    )
    channel.send(msg)

    # Step 1: current_timestep becomes 1, message scheduled for 2 -> not delivered yet
    d1 = channel.step()
    assert len(d1) == 0

    # Step 2: current_timestep becomes 2 -> delivered
    d2 = channel.step()
    assert len(d2) == 1
    assert d2[0].sender_id == "vehicle_1"


def test_channel_packet_loss():
    # Loss rate 1.0 means all messages dropped
    channel = CommunicationChannel(latency=0, packet_loss_rate=1.0, bandwidth_limit=None)
    msg = Message(
        priority=PriorityLevel.NORMAL,
        sender_id="vehicle_1",
        receiver_id="vehicle_2",
        timestamp=0,
        content={"pos": [0, 0]},
    )
    channel.send(msg)
    delivered = channel.step()
    assert len(delivered) == 0


def test_channel_invalid_packet_loss_rate():
    # Negative loss probability should raise ValueError
    with pytest.raises(ValueError, match="packet_loss_rate must be between 0.0 and 1.0"):
        CommunicationChannel(packet_loss_rate=-0.2)

    # Loss probability > 1.0 should raise ValueError
    with pytest.raises(ValueError, match="packet_loss_rate must be between 0.0 and 1.0"):
        CommunicationChannel(packet_loss_rate=1.5)

    # Negative latency should raise ValueError
    with pytest.raises(ValueError, match="latency must be non-negative"):
        CommunicationChannel(latency=-1)


def test_channel_bandwidth_limit_priority():
    channel = CommunicationChannel(latency=0, packet_loss_rate=0.0, bandwidth_limit=1)
    msg_routine = Message(
        priority=PriorityLevel.ROUTINE,
        sender_id="v1",
        receiver_id="v0",
        timestamp=0,
        content={"info": "routine"},
    )
    msg_critical = Message(
        priority=PriorityLevel.CRITICAL,
        sender_id="v2",
        receiver_id="v0",
        timestamp=0,
        content={"info": "emergency_brake"},
    )

    channel.send(msg_routine)
    channel.send(msg_critical)

    delivered = channel.step()
    # Bandwidth limit is 1, so only 1 message delivered, and it must be CRITICAL
    assert len(delivered) == 1
    assert delivered[0].priority == PriorityLevel.CRITICAL
    assert delivered[0].sender_id == "v2"
