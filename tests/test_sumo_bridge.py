"""
Unit tests for SUMO Network Generator and Traffic Simulator Bridge.
"""

import os
import xml.etree.ElementTree as ET
import pytest
from src.env.comm_channel import CommunicationChannel
from src.env.sumo_bridge import SumoNetworkGenerator, SumoTrafficBridge


def test_sumo_network_generator(tmp_path):
    output_dir = str(tmp_path / "sumo_net")
    files = SumoNetworkGenerator.create_intersection_scenario(output_dir, lane_length=80.0)

    assert os.path.exists(files["nod"])
    assert os.path.exists(files["edg"])
    assert os.path.exists(files["rou"])
    assert os.path.exists(files["cfg"])

    # Validate XML parsing
    nod_tree = ET.parse(files["nod"])
    assert nod_tree.getroot().tag == "nodes"
    nodes = {node.attrib["id"] for node in nod_tree.getroot().findall("node")}
    assert "center" in nodes
    assert "north" in nodes


def test_sumo_traffic_bridge_step_and_export(tmp_path):
    channel = CommunicationChannel(latency=0, packet_loss_rate=0.0)
    bridge = SumoTrafficBridge(comm_channel=channel, dt=0.1)
    bridge.initialize_scenario()

    assert len(bridge.vehicles) == 4
    assert bridge.vehicles["v_N"].active is True

    # Step with accelerations
    accelerations = {"v_N": 1.0, "v_S": -2.0, "v_E": 0.0, "v_W": 0.5}
    vehicles, collisions, delivered = bridge.step(accelerations)

    assert bridge.step_count == 1
    assert len(bridge.traces) == 4

    # Test FCD export
    fcd_file = str(tmp_path / "test_trace.fcd.xml")
    bridge.export_fcd_xml(fcd_file)
    assert os.path.exists(fcd_file)

    fcd_tree = ET.parse(fcd_file)
    assert fcd_tree.getroot().tag == "fcd-export"
    timestep = fcd_tree.getroot().find("timestep")
    assert timestep is not None
    assert len(timestep.findall("vehicle")) == 4
