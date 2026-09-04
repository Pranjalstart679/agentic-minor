# Communication-Aware Cooperative Agents in V2X

A multi-agent framework to evaluate and optimize cooperative autonomous vehicle coordination under non-stationary physical communication disruptions (latency, packet loss, bandwidth caps, and Rayleigh fading).

---

## Collaborator Quickstart and Project Guides

If you are joining the project, collaborating, or reviewing our work, start with our dedicated guides in the `docs/` folder:

- [Collaborator and Handover Guide](docs/COLLABORATOR_GUIDE.md): Plain-English walkthrough of what the project asked for in our Semester 5 minor proposal vs. what was implemented, evaluated, and published.
- [Documentation Hub](docs/README.md): Index of all detailed technical readables.
- [Architecture Deep Dive](docs/ARCHITECTURE_DEEP_DIVE.md): Mathematical formulations, Kalman filter mechanics, and MAPPO-GAT architecture.
- [Experiments and Scientific Results](docs/EXPERIMENTS_AND_RESULTS.md): 50-trial Monte Carlo ANOVA, Pareto frontiers, and mixed autonomy results.
- [Eclipse SUMO Co-Simulation Guide](docs/SUMO_SIMULATION_GUIDE.md): Microscopic simulation guide using SUMO and TraCI.
- [Viva and Defense Cheat Sheet](docs/VIVA_AND_DEFENSE_CHEATSHEET.md): 15 common defense questions with answers.
- [Interactive Web Dashboard](index.html): Open in any browser for live graphs and simulation replays.
- [Academic IEEE Manuscript](paper/main.pdf): Complete IEEE two-column publication draft.

---

## Executive Summary

In Vehicle-to-Everything (V2X) multi-agent systems, autonomous vehicles rely on wireless telemetry to coordinate safely at unsignalized intersections, roundabouts, and highway merges. However, real-world wireless channels suffer from:
- Latency (transmission and processing delays)
- Packet Loss (multipath fading, interference, and environmental noise)
- Bandwidth Bottlenecks (spectrum congestion and channel saturation)

### Key Contributions of This Framework
1. **Super-Additivity Proof (RQ1)**: A 50-trial Monte Carlo sweep and Welch's t-test ($t = 2.585, p = 0.0128 < 0.05$) statistically proving that combined network impairments degrade safety super-additively.
2. **Predictive Event-Triggered Communication (PET-Comm)**: A 6-state constant-acceleration Kalman Filter ($[x, y, v_x, v_y, a_x, a_y]^T$) with adaptive error thresholding that reduces communication bandwidth by 78% while eliminating collisions.
3. **Criticality-Aware Reliable Retransmission (CARR)**: Severity-based transport protocol with explicit ACK handshakes and priority queueing for emergency maneuvers.
4. **Mixed Autonomy Integration**: Simulates non-communicative human drivers using the Intelligent Driver Model (IDM) across penetration rates from 0% to 100%.
5. **Deep MARL with Graph Attention (MAPPO + GAT)**: Centralized training with decentralized execution, dynamically weighting neighbor risk to achieve a 91.9% relative collision reduction under extreme disruptions.
6. **Separating Axis Theorem (SAT) OBB Collisions**: Realistic 2D oriented rectangular bounding boxes ($4.5\text{ m} \times 2.0\text{ m}$) replacing simplified point mass approximations.
7. **Eclipse SUMO Co-Simulation Bridge**: Validated against industry-standard microscopic traffic tooling via TraCI.

---

## Repository Structure

```text
agents-minor/
├── docs/                               # All guides and readables
│   ├── README.md                       # Documentation hub
│   ├── COLLABORATOR_GUIDE.md           # Master handover guide for teammates
│   ├── ARCHITECTURE_DEEP_DIVE.md       # Technical algorithms and math
│   ├── EXPERIMENTS_AND_RESULTS.md      # Experimental benchmarks and tables
│   ├── SUMO_SIMULATION_GUIDE.md        # Eclipse SUMO bridge guide
│   └── VIVA_AND_DEFENSE_CHEATSHEET.md  # Q&A for project defense
│
├── src/                                # Core codebase
│   ├── env/                            # Traffic physics and wireless channel
│   │   ├── traffic_env.py              # 2D continuous traffic kinematics and SAT OBB
│   │   ├── comm_channel.py             # Latency, loss, bandwidth queue, Rayleigh fading
│   │   └── sumo_bridge.py              # Bridge to Eclipse SUMO traffic engine
│   ├── agents/                         # Agent controllers
│   │   ├── base_agent.py               # Abstract base agent class
│   │   ├── rule_agent.py               # Baseline cooperative agent
│   │   ├── pet_comm_agent.py           # PET-Comm agent
│   │   ├── carr_agent.py               # CARR protocol agent
│   │   ├── idm_human_agent.py          # IDM human-driven vehicle agent
│   │   ├── gat_layer.py                # Graph Attention Network PyTorch layer
│   │   └── mappo_agent.py              # MAPPO Actor-Critic neural network
│   ├── estimation/                     # State estimation
│   │   └── kalman_filter.py            # 6-state constant-acceleration Kalman Filter
│   └── orchestrator/                   # Orchestrator
│       └── hybrid_pipeline.py          # Pipeline for benchmark runs
│
├── experiments/                        # Scientific benchmark runners
│   ├── run_statistical_anova.py        # 50-trial Monte Carlo ANOVA validation
│   ├── run_mixed_autonomy_benchmarks.py# Sweeps across CAV penetration rates
│   ├── run_sensitivity_ablation_grid.py# Parameter sensitivity sweeps
│   ├── train_mappo.py                  # Training script for MAPPO Deep RL
│   ├── run_sumo_sim.py                 # Runner for SUMO microscopic simulation
│   ├── render_simulation_video.py      # MP4 simulation video renderer
│   └── results/                        # Generated charts and raw JSON data
│
├── paper/                              # Academic manuscript
│   ├── main.tex                        # Full IEEE 2-column LaTeX source
│   ├── main.pdf                        # Compiled camera-ready PDF
│   └── references.bib                  # BibTeX references
│
├── tests/                              # Automated test suite
│   ├── test_comm_channel.py            # Channel impairment tests
│   ├── test_category1_novelties.py     # SAT OBB, AoI, and Rayleigh fading tests
│   └── test_sumo_bridge.py             # SUMO bridge and mock engine tests
│
├── index.html                          # Interactive web dashboard
├── requirements.txt                    # Project dependencies
└── Sem-5th minor.pdf                   # Original Semester 5 minor proposal deck
```

---

## Setup and Quickstart

```bash
# 1. Activate Python virtual environment
.venv\Scripts\activate   # On Windows (PowerShell / Command Prompt)
# or: source .venv/bin/activate on Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run all unit tests
pytest tests/ -v

# 4. Open the interactive dashboard
start index.html         # On Windows
```

---

## Project Supervisors and Authors
- **Supervisors**: Dr. Alaa Daoud and Prof. KG Srinivasa
- **Institution**: Dr. Shyama Prasad Mukherjee International Institute of Information Technology, Naya Raipur (IIIT Naya Raipur)
- **Group Members**: Aryan Dubey, Pranjal Gupta, Swagata Barik
