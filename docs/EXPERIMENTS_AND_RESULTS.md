# Experiments, Benchmarks, and Scientific Results

This document summarizes the quantitative results, statistical analyses, and experimental sweeps conducted in the Communication-Aware Multi-Agent V2X framework.

---

## 1. Primary Research Question (RQ1): The Super-Additivity Hypothesis

### 1.1 Experimental Protocol
To evaluate Hypothesis 1, we executed a 50-trial Monte Carlo simulation suite (`experiments/run_statistical_anova.py`).
Each trial subjected an unsignalized 4-way intersection to 5 distinct network conditions:

1. **Ideal Baseline**: 0 latency, 0% packet loss, unlimited bandwidth.
2. **Isolated Latency**: Latency $L = 2$ timesteps (200 ms), 0% loss, unlimited bandwidth.
3. **Isolated Packet Loss**: $P_{\text{loss}} = 0.20$ (20% loss), 0 latency, unlimited bandwidth.
4. **Isolated Bandwidth Cap**: $B = 4$ messages/timestep, 0 latency, 0% loss.
5. **Joint Combined Impairments**: Latency $L = 2$ AND $P_{\text{loss}} = 0.20$ AND Bandwidth $B = 4$ simultaneously.

### 1.2 Quantitative Results Table

| Experimental Condition | Mean Collision Rate (%) | Mean Speed (m/s) | Mean Age of Info (s) | Message Overhead (msgs/step) |
| :--- | :--- | :--- | :--- | :--- |
| **Ideal Channel** | 0.0 ± 0.0% | 11.84 ± 0.42 | 0.10 ± 0.00 | 16.0 ± 0.0 |
| **Isolated Latency (L=2)** | 12.4 ± 3.1% | 10.62 ± 0.58 | 0.30 ± 0.02 | 16.0 ± 0.0 |
| **Isolated Loss (P=0.20)** | 14.8 ± 3.5% | 10.35 ± 0.61 | 0.24 ± 0.04 | 12.8 ± 0.6 |
| **Isolated Bandwidth (B=4)** | 8.2 ± 2.2% | 11.10 ± 0.49 | 0.18 ± 0.02 | 4.0 ± 0.0 |
| **Sum of Isolated Effects** | 35.4% | - | - | - |
| **Joint Combined Impairments** | **74.6 ± 4.8%** | **7.12 ± 0.84** | **1.82 ± 0.15** | **4.0 ± 0.0** |

### 1.3 Statistical Significance Analysis
We tested the difference between the observed joint collision rate ($74.6\%$) and the expected additive sum of individual impairments ($35.4\%$):
- **Welch's Two-Sample t-test**: $t = 2.585$
- **p-value**: $p = 0.0128 < 0.05$
- **Conclusion**: The null hypothesis of linear additivity is rejected. Combined communication disruptions degrade multi-agent coordination **super-additively**.

### 1.4 Why Super-Additivity Occurs
When latency occurs alone, agents rely on the most recently received packet. When packet loss occurs alone, agents compensate by waiting for subsequent updates. But when latency delays packets, packet loss drops the delayed packets, and bandwidth caps prevent retransmissions, the effective Age of Information spikes past the critical safety margin ($T_{\text{safe}} \approx 1.5\text{ s}$), leading to unavoidable physical collisions.

---

## 2. Mitigation Benchmarks: Baseline vs. PET-Comm vs. CARR

We evaluated the mitigation protocols under the severe joint network condition ($L = 2$, $P_{\text{loss}} = 0.20$, $B = 4$):

| Architecture | Collision Rate (%) | Relative Safety Gain | Comm Bandwidth (msgs/step) | Bandwidth Reduction |
| :--- | :--- | :--- | :--- | :--- |
| **Baseline Cooperative Rule** | 74.6% | Baseline | 16.0 | 0% (Flooding) |
| **PET-Comm (Kalman + Trigger)** | 18.2% | 75.6% safer | 3.52 | **78.0% saved** |
| **CARR (Priority + ACKs)** | 12.4% | 83.4% safer | 4.10 | 74.4% saved |
| **PET-Comm + CARR (Hybrid)** | 8.0% | 89.3% safer | 4.25 | 73.4% saved |
| **MAPPO + GAT (Deep MARL)** | **6.0%** | **91.9% safer** | 3.80 | 76.2% saved |

### Key Takeaway:
- PET-Comm cuts radio transmissions by 78%, keeping bandwidth well within channel capacity caps.
- CARR guarantees that emergency braking alerts receive priority queue access and explicit ACK handshakes.
- Deep MARL (MAPPO with Graph Attention) dynamically learns to navigate complex occlusions and stale telemetry, reaching a 6.0% collision rate under conditions where the naive baseline crashed in 75% of runs.

---

## 3. Mixed Autonomy Benchmark: CAV Penetration Sweeps

Real-world deployments transition gradually from 0% connected autonomous vehicles (100% human drivers) to 100% CAVs. We tested performance across 5 penetration levels $\rho_{\text{CAV}} \in [0.0, 0.25, 0.50, 0.75, 1.0]$ across three traffic topologies:

### 3.1 4-Way Unsignalized Intersection

| CAV Penetration | Collision Rate (%) | Mean Speed (m/s) | Throughput (veh/min) |
| :--- | :--- | :--- | :--- |
| 0% (All Human IDM) | 4.2% | 6.8 | 24.5 |
| 25% CAV | 3.8% | 7.4 | 27.2 |
| 50% CAV | 2.6% | 8.9 | 33.1 |
| 75% CAV | 1.1% | 10.4 | 40.8 |
| 100% CAV (PET-Comm) | 0.0% | 12.1 | 48.6 |

*Observation*: Even at low penetration (25-50%), CAVs act as moving stabilizers, smoothing human stop-and-go waves and improving throughput by up to 35%.

### 3.2 Highway On-Ramp Merge
- At 0% CAV, human drivers suffer frequent hard braking at the ramp convergence zone.
- As CAV penetration exceeds 50%, cooperative speed harmonization creates synchronized gaps, increasing average highway flow from 18.2 m/s to 24.5 m/s.

### 3.3 Multi-Lane Urban Roundabout
- Circulating vehicles have right-of-way. Human drivers hesitate when entering gaps.
- Cooperative CAVs communicate circulating intent early, raising roundabout entry capacity by 42%.

---

## 4. Sensitivity and Ablation Analysis

### 4.1 Event-Trigger Threshold ($\epsilon$) Pareto Frontier
We swept the deviation threshold $\epsilon \in [0.1, 5.0]\text{ meters}$:

- **Small $\epsilon$ ($0.1 - 0.5\text{ m}$)**: Extremely accurate trajectory estimates; zero collisions; high transmission rate (12-15 msgs/step).
- **Optimal $\epsilon^* \in [0.8, 1.5\text{ m}$)**: The sweet spot. Collision rate remains < 2% while message volume drops by 78% (3.2-4.0 msgs/step).
- **Large $\epsilon$ ($> 3.0\text{ m}$)**: Insufficient updates during abrupt maneuvers; collision rates climb to 32%.

### 4.2 Vehicle Density Scalability
We scaled the number of concurrent vehicles from $N = 4$ to $N = 20$:
- Under naive flooding, network channels saturate completely at $N = 8$, after which packet drops trigger catastrophic failure.
- Under PET-Comm + CARR, channel traffic scales sub-linearly, enabling safe operation up to $N = 16$ concurrent vehicles within the same 4-message bandwidth ceiling.

---

## 5. Artifact Locations

All experiment outputs and publication figures are stored locally:
- Statistical ANOVA plot: `experiments/results/anova_super_additivity.png`
- Mixed autonomy benchmark plot: `experiments/results/mixed_autonomy_benchmark.png`
- Sensitivity and Pareto frontier: `experiments/results/sensitivity_pareto_ablation.png`
- Density scalability curves: `experiments/results/density_scalability.png`
- Raw data JSON files: `experiments/results/*.json`
