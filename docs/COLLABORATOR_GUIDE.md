# Project Handover and Collaborator Guide

## Welcome to the Project
Welcome to the repository for **Communication-Aware Cooperative Multi-Agent Systems in V2X Transportation**.

This guide is written specifically for project partners, collaborators, and team members (Aryan Dubey, Pranjal Gupta, Swagata Barik, and reviewing faculty) to quickly understand:
1. What the project was originally asked to do (from our Semester 5 Minor proposal presentation).
2. The core concepts in intuitive, plain English.
3. What has been fully built, implemented, and proven.
4. How the entire codebase is organized.
5. How to run simulations, view the dashboard, execute tests, and reproduce findings.
6. A quick defense and viva cheat sheet for presentations.

---

## 1. The Big Picture: What Problem Are We Solving?

### The Real-World Scenario
Imagine an urban 4-way intersection without traffic lights, or a busy highway on-ramp. Several connected autonomous vehicles (CAVs) approach at 40-50 km/h from different directions.
If vehicles can communicate with one another using Vehicle-to-Vehicle (V2V) wireless radio, they can coordinate smoothly: vehicle A yields slightly, vehicle B accelerates, and they cross safely without coming to a complete stop. This reduces congestion, saves fuel, and prevents accidents.

### The Problem in Existing Research
Most existing academic papers and textbook algorithms make an unrealistic assumption: they assume wireless communication is **perfect**. They assume:
- Zero transmission delay (instant messages).
- Zero packet loss (no dropped messages).
- Unlimited bandwidth (cars can broadcast huge messages every millisecond).

### Reality: Wireless Networks Are Unreliable
In real-world transportation networks:
- **Bandwidth Limits**: The wireless spectrum is shared and limited. If dozens of cars broadcast high-rate messages at the same time, network queues overflow.
- **Latency**: Signal processing and queueing introduce delays ranging from 50 ms to several hundred milliseconds. By the time a car receives a message saying "I am braking", it may already be too late.
- **Packet Loss and Fading**: Buildings, rain, distance, and multipath radio interference (Rayleigh fading) cause radio signals to weaken and packets to drop randomly.

### The Research Question
When latency, packet loss, and bandwidth limits happen **at the exact same time**, what happens to coordinating cars? And how can we design intelligent vehicles that stay 100% safe even when communication breaks down?

---

## 2. What the Project Originally Asked (The Initial Proposal)

In our initial Semester 5 minor proposal presentation (`Sem-5th minor.pdf`), presented on August 25, 2026 to supervisors Dr. Alaa Daoud and Prof. KG Srinivasa, we established:

### A. The Core Research Gap
- Existing benchmarks (such as AgentComm-Bench, TMC, IntNet, and ETCNet) only test one communication failure at a time (only latency, or only packet loss), or they test only on toy grid games and video games (like StarCraft) rather than real transportation physics.
- No prior work systematically evaluated cooperative driving under **joint, simultaneous network disruptions** using an interpretable agent framework.

### B. The Primary Research Question (RQ1)
> *"In a cooperative transportation coordination task, how does coordination performance and collision risk degrade under combined communication impairments (packet loss, latency, and bandwidth limitation applied jointly) compared to each impairment tested in isolation?"*

**The Super-Additivity Hypothesis**:
We hypothesized that combined network impairments cause damage that is **super-additive** (meaning the combined failure is far worse than simply adding the individual failure percentages together). When messages are delayed AND packets are lost AND bandwidth is choked, vehicle safety buffers collapse exponentially.

### C. What Was Proposed as "Future Work" in the Proposal
In the initial proposal (`Sem-5th minor.pdf`), the presentation outlined three ambitious directions as future work:
1. **Idea 1 — Predictive Event-Triggered Communication (PET-Comm)**: Use Kalman filtering to predict neighbors' trajectories locally. Only transmit when reality deviates from prediction, cutting bandwidth usage.
2. **Idea 2 — Criticality-Aware Reliable Retransmission (CARR)**: Upgrade emergency braking messages to high priority and require explicit acknowledgment (ACK) packets with retransmissions.
3. **Advanced Intelligence**: Transition to Deep Multi-Agent Reinforcement Learning (MARL) and incorporate human driver behavior (mixed autonomy).

---

## 3. What We Have Built and Accomplished

Rather than leaving the proposed ideas as theoretical future work, **we implemented and evaluated every single proposed component**. Here is the breakdown:

### Summary Comparison: Proposal vs. Finished Implementation

| Proposal Goal / Focus Area | What Was Asked | What We Implemented and Delivered |
| :--- | :--- | :--- |
| **Physics and Traffic Environment** | Unsignalized intersection simulation | Built continuous 2D kinematics with 3 topologies (4-way intersection, highway merge, roundabout) plus exact Separating Axis Theorem (SAT) oriented bounding box collisions. |
| **Wireless Channel Model** | Basic latency, loss, and bandwidth cap | Realistic channel with latency buffer, Bernoulli loss, priority min-heap bandwidth queue, and physical Rayleigh fading with log-normal path loss. |
| **RQ1: Hypothesis Testing** | Test whether combined impairments degrade super-additively | Executed 50-trial Monte Carlo ANOVA suite. Welch's t-test confirmed super-additivity with statistical significance (p = 0.0128 < 0.05). |
| **Idea 1: PET-Comm** | Conceptual proposal in future work | Fully implemented 6-state 2D Constant Acceleration Kalman Filter with adaptive error thresholding; reduced message overhead by 78% while maintaining zero collisions. |
| **Idea 2: CARR** | Conceptual proposal in future work | Fully implemented priority queue with Time-to-Collision (TTC) severity classification, explicit ACKs, and exponential backoff retransmission. |
| **Mixed Autonomy (Human Drivers)** | Mentioned in proposed future work | Implemented Intelligent Driver Model (IDM) for non-communicative human vehicles with visual line-of-sight yielding; tested 0% to 100% CAV penetration. |
| **Deep MARL** | Mentioned in proposed future work | Implemented and trained MAPPO (Multi-Agent PPO) with Graph Attention Networks (GAT); achieved 94% collision rate reduction under extreme disruptions. |
| **Microscopic Verification** | Suggested during defense prep | Built an Eclipse SUMO co-simulation bridge (`sumo_bridge.py` and `run_sumo_sim.py`) for microscopic traffic simulator validation. |
| **Academic Deliverables** | Project report | Authored complete IEEE 2-column LaTeX manuscript (`paper/main.tex` and `paper/main.pdf`), interactive web dashboard (`index.html`), and video simulation renderer. |

---

## 4. Detailed Breakdown of Core Innovations

### 1. Realistic Traffic Physics and Physical Collision Detection (`src/env/traffic_env.py`)
- Standard academic code often treats cars as zero-dimensional points or circles. If two points get within 2 meters, it counts as a crash.
- Our implementation models vehicles as real physical rectangles (4.5 m by 2.0 m).
- We implemented the **Separating Axis Theorem (SAT)** for Oriented Bounding Boxes (OBB). If two rotated rectangles overlap by even a millimeter, a physical collision is detected.
- Real-time **Age of Information (AoI)** tracking measures how many seconds old the situational data is for every surrounding vehicle.
- Supported scenarios:
  - 4-way unsignalized intersection (`spawn_intersection_scenario`)
  - Highway on-ramp merge (`spawn_highway_merge_scenario`)
  - Multi-lane urban roundabout (`spawn_roundabout_scenario`)

### 2. Physical Wireless Channel Simulator (`src/env/comm_channel.py`)
- **Latency**: Implemented a discrete timestep FIFO queue that delays message arrival.
- **Packet Loss**: Stochastic packet dropping based on channel noise.
- **Bandwidth Limits**: Strict limits on how many messages can be transmitted per timestep, ordered by a min-heap priority queue.
- **Rayleigh Fading and Path Loss**: Uses physical radio propagation laws:
  As distance increases, signal strength drops and packet loss probability spikes.

### 3. The 6-State Kalman Filter Trajectory Predictor (`src/estimation/kalman_filter.py`)
- Tracks each neighbor's continuous state vector:
  [x, y, v_x, v_y, a_x, a_y]^T
- Combines kinematic transition matrices with measurement update matrices.
- Enables vehicles to predict where other cars will be several seconds into the future even if communication is silent or temporarily dropped.

### 4. PET-Comm: Predictive Event-Triggered Communication (`src/agents/pet_comm_agent.py`)
- Instead of spamming broadcasts every 100 ms, vehicles run a local Kalman Filter predicting what other cars expect them to do.
- The car checks the difference between its true position and its predicted position:
  Difference = || p_actual - p_predicted ||
- If the difference is smaller than threshold epsilon, **no message is transmitted**. The network remains silent, saving precious radio bandwidth.
- When an unexpected maneuver occurs (sudden acceleration or turn), the threshold is exceeded and a state update is broadcast immediately.
- **Result**: 78% reduction in network bandwidth consumption with zero safety compromise.

### 5. CARR: Criticality-Aware Reliable Retransmission (`src/agents/carr_agent.py`)
- Evaluates the Time-to-Collision (TTC) with all surrounding vehicles.
- If a potential collision is detected within a dangerous safety threshold, the message is tagged with **CRITICAL** priority.
- Critical messages bypass ordinary traffic in the queue and require an explicit **Acknowledgment (ACK)** from the receiving vehicle.
- If the ACK is lost, the agent retransmits the warning using an exponential backoff schedule.

### 6. Mixed Autonomy with Human Drivers (`src/agents/idm_human_agent.py`)
- Real roads will not have 100% autonomous cars overnight.
- We modeled regular human drivers using the **Intelligent Driver Model (IDM)**, incorporating comfortable braking, human reaction times, and visual field-of-view yielding.
- Human drivers do not have V2X radios. Autonomous vehicles detect them using simulated onboard sensors and adjust coordination accordingly.
- Tested across penetration rates from 0% (all humans) to 100% (all CAVs).

### 7. Deep MARL with Graph Attention Networks (`src/agents/mappo_agent.py`, `src/agents/gat_layer.py`)
- Designed a centralized training with decentralized execution (CTDE) architecture using **Multi-Agent PPO (MAPPO)**.
- Integrated a **Graph Attention Network (GAT)** layer. The attention weights learn which neighboring vehicles pose the highest immediate risk under degraded communication.
- Trained actor and critic networks to optimize speed while strictly penalizing collisions and high AoI.
- Achieved a **6.0% collision rate** under extreme network disruption where baseline rule-based systems suffered an 88-100% collision rate (a 94% relative reduction).

### 8. Statistical Proof of Super-Additivity (`experiments/run_statistical_anova.py`)
- Ran a 50-trial Monte Carlo simulation sweep comparing:
  1. Ideal channel (0% loss, 0 delay, unlimited bandwidth)
  2. Isolated latency (delay only)
  3. Isolated packet loss (drop only)
  4. Isolated bandwidth cap (bandwidth only)
  5. Joint combined impairments (all three simultaneously)
- Measured Welch's t-test: t = 2.585, p = 0.0128 < 0.05.
- Statistically proves that combined impairments degrade coordination super-additively.

---

## 5. Codebase Directory Map

Here is the repository layout to help you navigate:

```text
agents-minor/
├── docs/                               # All documentation and readables
│   ├── README.md                       # Documentation hub and index
│   ├── COLLABORATOR_GUIDE.md           # This file: Project overview and handover
│   ├── ARCHITECTURE_DEEP_DIVE.md       # Detailed technical and algorithmic guide
│   ├── EXPERIMENTS_AND_RESULTS.md      # Analysis of empirical benchmarks and graphs
│   ├── SUMO_SIMULATION_GUIDE.md        # Guide for SUMO co-simulation
│   └── VIVA_AND_DEFENSE_CHEATSHEET.md  # Q&A for presentations and viva examinations
│
├── src/                                # Core implementation
│   ├── env/                            # Environment and networking
│   │   ├── traffic_env.py              # 2D continuous traffic physics and SAT collision
│   │   ├── comm_channel.py             # Realistic wireless network impairment channel
│   │   └── sumo_bridge.py              # Bridge to Eclipse SUMO traffic simulator
│   ├── agents/                         # Vehicle controller agents
│   │   ├── base_agent.py               # Abstract base agent class
│   │   ├── rule_agent.py               # Baseline cooperative agent
│   │   ├── pet_comm_agent.py           # Predictive Event-Triggered Communication
│   │   ├── carr_agent.py               # Criticality-Aware Reliable Retransmission
│   │   ├── idm_human_agent.py          # Intelligent Driver Model (human vehicles)
│   │   ├── gat_layer.py                # Graph Attention Network PyTorch layer
│   │   └── mappo_agent.py              # MAPPO Actor-Critic neural network
│   ├── estimation/                     # State estimation
│   │   └── kalman_filter.py            # 6-state constant acceleration Kalman Filter
│   └── orchestrator/                   # Simulation runners
│       └── hybrid_pipeline.py          # Pipeline executing comparative benchmarks
│
├── experiments/                        # Scientific benchmark runners
│   ├── run_statistical_anova.py        # 50-trial Monte Carlo ANOVA validation
│   ├── run_mixed_autonomy_benchmarks.py# Tests varying CAV penetration rates
│   ├── run_sensitivity_ablation_grid.py# Parameter sweeps (epsilon, latency, density)
│   ├── train_mappo.py                  # Training loop for MAPPO deep RL
│   ├── run_sumo_sim.py                 # Runner for SUMO microscopic simulation
│   ├── render_simulation_video.py      # Generates MP4 video from simulation steps
│   └── results/                        # Raw JSON results and publication plots
│
├── paper/                              # Academic paper
│   ├── main.tex                        # Full IEEE 2-column LaTeX manuscript
│   ├── main.pdf                        # Compiled camera-ready PDF
│   └── references.bib                  # BibTeX bibliography
│
├── tests/                              # Unit and integration test suite
│   ├── test_comm_channel.py            # Tests for latency, loss, and bandwidth
│   ├── test_category1_novelties.py     # Tests for SAT OBB, AoI, and Rayleigh fading
│   └── test_sumo_bridge.py             # Tests for SUMO bridge integration
│
├── index.html                          # Interactive web dashboard and visualizer
├── requirements.txt                    # Project dependencies
└── README.md                           # Repository introduction
```

---

## 6. How to Run Everything (Quickstart)

### Step 1: Environment Setup
Open a terminal (PowerShell, Command Prompt, or bash) in the project directory:

```bash
# Activate existing virtual environment
.venv\Scripts\activate   # On Windows
# or: source .venv/bin/activate on Linux/macOS

# Install dependencies (if needed)
pip install -r requirements.txt
```

### Step 2: Run Unit Tests
Verify all components are working properly:

```bash
pytest tests/ -v
```
All unit tests should pass.

### Step 3: View the Interactive Web Dashboard
Launch the web dashboard in your browser to inspect interactive graphs and visual simulation replays:

```bash
# Open directly in your browser:
start index.html         # On Windows
# or: open index.html    # On macOS
# or: xdg-open index.html # On Linux
```

### Step 4: Run Statistical ANOVA Experiments
To reproduce the 50-trial Monte Carlo analysis proving the Super-Additivity hypothesis:

```bash
python experiments/run_statistical_anova.py
```
Outputs are saved in `experiments/results/anova_super_additivity.png`.

### Step 5: Run Mixed Autonomy Benchmark
To test different ratios of human drivers versus autonomous vehicles across intersection, highway, and roundabout topologies:

```bash
python experiments/run_mixed_autonomy_benchmarks.py
```

### Step 6: Render a Video of the Vehicle Simulation
To generate an MP4 video showing vehicles crossing the intersection under degraded communication:

```bash
python experiments/render_simulation_video.py
```

---

## 7. Viva and Presentation Cheat Sheet

If a professor or evaluator asks you about the project, here are the key answers:

### Q1: What makes this project unique compared to prior papers?
**Answer**: Prior benchmarks (like AgentComm-Bench or TMC) either test communication failures in isolation (only loss or only delay) or evaluate them on abstract toy grid worlds and video games. We are the first to systematically evaluate combined, simultaneous physical network disruptions (latency + loss + bandwidth caps + Rayleigh fading) on realistic continuous traffic kinematics with oriented bounding box collisions.

### Q2: What is "Super-Additivity"?
**Answer**: When you test 20% packet loss alone, cars can still manage (say, 10% collisions). When you test 2-step latency alone, cars can also adapt (say, 8% collisions). But when you apply both simultaneously along with bandwidth limits, the collision rate jumps to over 70%. The degradation is strictly greater than the sum of the individual parts (p = 0.0128), because the recovery mechanism for latency (relying on recent packets) is broken by packet loss, and the recovery mechanism for packet loss (retransmissions) is blocked by bandwidth throttling.

### Q3: How does PET-Comm save 78% bandwidth without causing accidents?
**Answer**: Vehicles run a 6-state Kalman Filter tracking positions, velocities, and accelerations of their neighbors. If an autonomous vehicle is maintaining a constant acceleration or following its planned trajectory, it sends zero messages because other cars can already predict its location. It only transmits a packet when its actual position diverges from the prediction by more than threshold epsilon.

### Q4: What happens when a human-driven vehicle enters the intersection?
**Answer**: Human drivers are modeled using the Intelligent Driver Model (IDM) and line-of-sight visual yielding. Because humans do not have V2X radios, our CAVs detect them using simulated range sensors, treat them as non-communicative dynamic obstacles, and yield right-of-way based on physical time-to-arrival.

### Q5: Why did you use MAPPO and Graph Attention Networks?
**Answer**: Heuristic rules struggle when vehicle density increases or network conditions vary unpredictably. GAT dynamically assigns attention weights to neighboring cars based on relative distance, speed, and Age of Information (AoI). MAPPO trains the vehicles in a centralized manner with complete state information while executing purely decentralized control on each vehicle using only its local and received information.

---

## 8. Where to Go Next

- For a deep dive into the mathematical formulations and state machines, read [ARCHITECTURE_DEEP_DIVE.md](ARCHITECTURE_DEEP_DIVE.md).
- For complete charts, tables, and numerical results, read [EXPERIMENTS_AND_RESULTS.md](EXPERIMENTS_AND_RESULTS.md).
- For instructions on running the Eclipse SUMO bridge, read [SUMO_SIMULATION_GUIDE.md](SUMO_SIMULATION_GUIDE.md).
- To prepare for project defenses and questions, review [VIVA_AND_DEFENSE_CHEATSHEET.md](VIVA_AND_DEFENSE_CHEATSHEET.md).
- To read the academic manuscript, see the compiled PDF in [paper/main.pdf](../paper/main.pdf).
