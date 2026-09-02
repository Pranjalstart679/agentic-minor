---
name: communication-aware-marl
description: |
  Guide and operational procedures for developing, benchmarking, and evaluating
  Communication-Aware Multi-Agent Cooperative Frameworks under realistic V2X physical channel disruptions
  (latency, packet loss, bandwidth bottlenecks, and Rayleigh fading).

  Use this skill when modifying traffic environment kinematics, communication channels,
  trajectory estimators (Kalman Filter), event-triggered policies (PET-Comm), or priority protocols (CARR).
---

# Communication-Aware Multi-Agent Cooperative Framework Guide

This skill provides step-by-step procedures for managing and expanding the `agents-minor` research project.

## Core Architectural Components

1. **Physical Wireless Channel** (`src/env/comm_channel.py`):
   - **Propagation Latency**: Message queuing with delivery delay $L$ timesteps.
   - **Rayleigh Fading & Path Loss**: Effective loss rate $P_{\text{loss, effective}} = \min(0.99, P_{\text{base}} + 1 - \exp(-f_{\text{fade}} / (1 + R)))$ where $f_{\text{fade}} = (d / d_0)^\eta$.
   - **Min-Heap Priority Bandwidth Limitation**: Truncates queued messages per timestep to bandwidth cap $B$, prioritizing `CRITICAL` over `ROUTINE` priority messages.

2. **Kinematic Traffic Simulation** (`src/env/traffic_env.py`):
   - **4-Way Unsignalized Intersection**: `spawn_default_scenario(randomized=True)`
   - **Highway High-Speed Merging**: `spawn_highway_merge_scenario(num_mainline=3, num_ramps=2)`
   - **Collision Safety Threshold**: Vehicles closer than $3.0\text{m}$ trigger collision flags.

3. **Trajectory Estimation** (`src/estimation/kalman_filter.py`):
   - 2D Constant Acceleration Kalman Filter tracking state vector:
     $$\mathbf{x} = [x, y, v_x, v_y, a_x, a_y]^T$$
   - Used by PET-Comm agents to estimate neighbor positions during packet drop intervals up to safety horizon $T_{\text{safe}}$.

4. **Event-Triggered Policy** (`src/agents/pet_comm_agent.py`):
   - Transmits state vectors only when position deviation exceeds event threshold:
     $$\|\mathbf{p}_i(t) - \hat{\mathbf{p}}_i(t)\| > \epsilon$$

---

## Standard Execution & Testing Workflows

### 1. Run Pytest Suite
```bash
.\.venv\Scripts\python.exe -m pytest tests/
```

### 2. Run RQ1 Impairment Benchmark
```bash
.\.venv\Scripts\python.exe experiments/run_rq1_combined_tests.py
```

### 3. Run 50-Trial Statistical ANOVA & Welch's T-Test
```bash
.\.venv\Scripts\python.exe experiments/run_statistical_anova.py
```

### 4. Run Mitigation Comparison (Rule vs PET-Comm vs CARR)
```bash
.\.venv\Scripts\python.exe experiments/run_mitigation_tests.py
```

---

## Research Best Practices

- Always run 50+ randomized seed trials before claiming statistical significance ($p < 0.05$).
- Maintain zero emojis in README files and markdown documentation.
- Update `TIMELINE.md` and `index.html` whenever new empirical benchmarks or code modules are added.
