# Eclipse SUMO Co-Simulation Guide

This document explains how the framework integrates with **Eclipse SUMO (Simulation of Urban MObility)** for microscopic traffic simulation validation.

---

## 1. Why SUMO Integration?

While our custom 2D simulator (`src/env/traffic_env.py`) provides rapid, exact kinematic simulation with physical OBB bounding boxes and custom network channels, evaluating algorithms inside an industry-standard open-source traffic suite like Eclipse SUMO provides:
1. Microscopic vehicle dynamics verified by the transportation research community.
2. Standard road network representations (OpenStreetMap, `.net.xml`).
3. Seamless extension to city-scale traffic networks.

---

## 2. Architecture of the SUMO Bridge (`src/env/sumo_bridge.py`)

The bridge connects Python control algorithms to SUMO using the Traffic Control Interface (**TraCI**):

```text
+-----------------------+                    +-------------------------+
| Python Controller     |                    | Eclipse SUMO Engine     |
| - TrafficEnv          |                    | (sumo / sumo-gui)       |
| - CommChannel         |  TraCI Protocol    |                         |
| - PET-Comm / CARR     | <================> | - Microscopic Physics   |
| - Kalman Filter       |   TCP Socket       | - Lane Geometries       |
+-----------------------+                    | - Vehicle Dynamics      |
                                             +-------------------------+
```

### Key Capabilities:
- **Vehicle Injection**: Injects CAVs and human-driven vehicles into designated routes.
- **Speed and Acceleration Control**: Overrides default car-following algorithms via `traci.vehicle.setSpeed()` and `traci.vehicle.slowDown()`.
- **Telemetry Extraction**: Reads continuous positions, velocities, and headings at each simulation step.
- **Fault-Tolerant Mock Fallback**: If SUMO is not installed on the host machine, the bridge automatically operates in a high-fidelity synthetic mock mode so all unit tests and CI pipelines run without errors.

---

## 3. Prerequisites and Installation

To run SUMO natively with graphical visualization:

### Windows:
1. Download SUMO from the official site: https://eclipse.dev/sumo/
2. Run the Windows installer and ensure `SUMO_HOME` is added to your environment variables.
3. Verify in PowerShell:
   ```bash
   sumo --version
   ```

### Linux (Ubuntu/Debian):
```bash
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-gui
export SUMO_HOME="/usr/share/sumo"
```

### Python Package:
Install TraCI (included in `requirements.txt`):
```bash
pip install traci
```

---

## 4. Running the SUMO Co-Simulation

### 4.1 Running via the Experiment Script
Execute the dedicated SUMO benchmark script:

```bash
python experiments/run_sumo_sim.py
```

Options:
- `--gui`: Launches the graphical SUMO interface (`sumo-gui`) to visually inspect cars moving through the intersection.
- `--steps`: Number of simulation timesteps to run (default: 500).
- `--cav-ratio`: Proportion of vehicles equipped with V2X (0.0 to 1.0).
- `--impairments`: Enables latency, packet loss, and bandwidth limits on the V2X link.

Example command with GUI:
```bash
python experiments/run_sumo_sim.py --gui --cav-ratio 0.75 --steps 300
```

### 4.2 Running the Integration Tests
To test the SUMO bridge and mock engine:

```bash
pytest tests/test_sumo_bridge.py -v
```

All tests will execute and verify state extraction, vehicle stepping, and safe cleanup.
