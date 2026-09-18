---
name: mixed-autonomy-simulation
description: |
  Operational procedures for benchmarking mixed-autonomy traffic environments (Connected Autonomous Vehicles + IDM Human Drivers),
  multi-topology scaling (intersections, highway merges, roundabouts), and parameter sensitivity Pareto sweeps.

  Use this skill when configuring CAV penetration rates, IDM human parameters,
  traffic scenario generators, density scaling, or running ablation grid benchmarks.
---

# Mixed-Autonomy Simulation & Multi-Scenario Benchmarking Skill

This skill provides standard protocols for executing mixed-autonomy and multi-topology scaling experiments in `agents-minor`.

## Core Components

1. **Intelligent Driver Model (IDM) (`src/agents/idm_human_agent.py`)**:
   - Models human-driven vehicles (HDVs) that do not use V2X wireless communication.
   - Relies exclusively on local line-of-sight radar tracking (`update_sensor_vision`).
   - Differential longitudinal acceleration:
     $$a = a_{\text{max}} \left[ 1 - \left(\frac{v}{v_0}\right)^\delta - \left(\frac{s^*(v, \Delta v)}{s}\right)^2 \right]$$
     where:
     $$s^*(v, \Delta v) = s_0 + \max\left(0, vT + \frac{v \Delta v}{2\sqrt{a_{\text{max}} b_{\text{comf}}}}\right)$$

2. **Traffic Scenarios (`src/env/traffic_env.py`)**:
   - `spawn_scalable_intersection(num_vehicles)`: High-density 4-way unsignalized intersection ($N \in [4, 20]$).
   - `spawn_highway_merge_scenario(num_mainline, num_ramps)`: On-ramp merging under high mainline velocity.
   - `spawn_roundabout_scenario(num_circulating, num_approaching)`: 2-lane circular roundabout with yield-at-entry dynamics.

3. **CAV Penetration Rate Sweeps**:
   - Mixed-fleet distribution: $\rho_{\text{CAV}} \in [0.0, 0.25, 0.50, 0.75, 1.0]$.
   - Vehicles $i \le \lfloor N \cdot \rho_{\text{CAV}} \rfloor$ instantiate cooperative agents (Rule, PET-Comm, CARR, or MAPPO); remaining vehicles instantiate `IDMHumanAgent`.

---

## Standard Execution & Benchmark Workflows

### 1. Run Mixed Autonomy Sweep
Executes 30 trials per condition across multiple topologies and CAV penetration levels:
```bash
.\.venv\Scripts\python.exe experiments/run_mixed_autonomy_benchmarks.py
```
Outputs generated:
- Results JSON: `experiments/results/mixed_autonomy_results.json`
- Comparative Plots: `experiments/results/mixed_autonomy_benchmark.png`

### 2. Run Comprehensive Sensitivity & Ablation Grid
Performs full parameter sweeps over event-threshold $\epsilon \in [0.1, 5.0]$, latency $L$, loss $P_{\text{loss}}$, bandwidth $B$, and vehicle density $N$:
```bash
.\.venv\Scripts\python.exe experiments/run_sensitivity_ablation_grid.py
```
Outputs generated:
- Results JSON: `experiments/results/sensitivity_ablation_results.json`
- Pareto Frontier Plots: `experiments/results/sensitivity_pareto_ablation.png`
- Density Scalability Plots: `experiments/results/density_scalability.png`
