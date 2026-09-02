# Project Timeline & Activity Log

**Project Title**: Communication-Aware Cooperative Multi-Agent Frameworks  
**Supervisors**: Dr. Alaa Daoud & Prof. KG Srinivasa (IIIT Naya Raipur)  
**Team**: Aryan Dubey, Pranjal Gupta, Swagata Barik  
**Selected Strategy**: Option 4 - Comprehensive End-to-End Hybrid Framework  

---

## Log of Activities

### Phase 1: Project Scoping & Options Evaluation

* **Timestamp**: 2026-08-31 03:23 IST
* **Milestone**: Project Proposal & Scope Alignment
* **Action Taken**: Analyzed presentation deck (`Sem-5th minor.pdf`) and generated detailed implementation options in `PROJECT_OPTIONS.md`.
* **Rationale**: Identified core research gap in current literature (MARL frameworks only test isolated communication failures or toy environments). Proposed four distinct pathways for execution.
* **Outcome**: User selected Option 4 (End-to-End Hybrid Framework) combining baseline empirical degradation analysis with mitigation mechanisms (PET-Comm + CARR).

---

### Phase 2: Environment Setup & Architecture Definition

* **Timestamp**: 2026-08-31 03:32 IST
* **Milestone**: Workspace & Project Architecture Initialization
* **Action Taken**: 
  1. Initialized project directory tree: `src/env`, `src/agents`, `src/estimation`, `src/utils`, `experiments`, and `tests`.
  2. Created Python 3.12 virtual environment (`.venv`).
  3. Created dependency specification file (`requirements.txt`) including `numpy`, `scipy`, `matplotlib`, `torch`, `filterpy`, `pytest`.
  4. Created `README.md` without emojis following project global rules.
* **Rationale**: Standardized modular structure to cleanly separate environment dynamics, network channel perturbations, trajectory estimators, agent controllers, and experiment runners.

---

### Phase 3: Core Implementation & Algorithm Development

* **Timestamp**: 2026-08-31 03:35 IST
* **Milestone**: End-to-End Source Code Architecture Implementation
* **Action Taken**: 
  1. **Network Channel Module** (`src/env/comm_channel.py`): Built controllable latency ($L$), Bernoullian packet loss ($P_{\text{loss}}$), and priority min-heap bandwidth limiting ($B$).
  2. **Kinematics & Traffic Environment** (`src/env/traffic_env.py`): Created a 4-way unsignalized intersection multi-agent vehicle simulation with collision detection and traffic metrics.
  3. **State Estimation Module** (`src/estimation/kalman_filter.py`): Implemented 2D Constant Acceleration Kalman Filter ($[x, y, v_x, v_y, a_x, a_y]^T$).
  4. **Cooperative Agents**:
     * Baseline Rule-Based (`src/agents/rule_agent.py`): Continuous state broadcasting + Time-To-Collision (TTC) intersection yielding.
     * PET-Comm Agent (`src/agents/pet_comm_agent.py`): Predictive event-triggered communication ($\|x - \hat{x}\| > \epsilon$) + packet loss fallback.
     * CARR Agent (`src/agents/carr_agent.py`): Priority classification + explicit ACK retransmission for emergency events.
  5. **Experiment Pipelines**:
     * `experiments/run_rq1_combined_tests.py`: Runs 5 scenarios (Ideal, Latency-only, Loss-only, Bandwidth-only, Combined Joint) to answer RQ1.
     * `experiments/run_mitigation_tests.py`: Evaluates Rule Baseline vs PET-Comm vs CARR under severe combined impairments.
  6. **Unit Test Suite**: Created test coverage in `tests/test_comm_channel.py`, `tests/test_kalman_filter.py`, and `tests/test_agents.py`.
* **Rationale**: Fulfills all phases of Option 4, creating an end-to-end framework to conduct empirical evaluation of RQ1 and test slide 8 mitigation ideas.

---

### Phase 4: Execution & Empirical Verification

* **Timestamp**: 2026-08-31 03:36 IST
* **Milestone**: Unit Test Verification & Benchmark Results Generation
* **Action Taken**:
  1. Executed `pytest tests/`: All 9 unit tests passed cleanly (100% pass rate across channel, estimator, and agent modules).
  2. Executed `experiments/run_rq1_combined_tests.py`: Evaluated isolated vs. combined joint communication failure degradation across 5 scenarios.
  3. Executed `experiments/run_mitigation_tests.py`: Verified mitigation algorithms against severe combined network disruptions.
* **Findings & Key Results**:
  * **RQ1 Verification**: Unmitigated baseline agents suffer 100% collision rate when exposed to severe combined impairments ($L=2, P_{\text{loss}}=0.3, B=2$).
  * **Mitigation Performance**: **PET-Comm** (Predictive Event-Triggered Communication) successfully reduces collision rates from **100% down to 20%** under severe combined network disruptions by utilizing Kalman Filter trajectory estimates when packets are delayed/dropped.

---

### Phase 5: Deep MARL & Neural Graph Policies

* **Timestamp**: 2026-08-31 03:55 IST
* **Milestone**: Multi-Agent PPO (MAPPO) with Graph Attention Networks (GAT)
* **Action Taken**:
  1. Implemented `GraphAttentionLayer` in `src/agents/gat_layer.py`.
  2. Implemented Centralized Critic and Decentralized Actor in `src/agents/mappo_agent.py`.
  3. Trained Actor-Critic policy using GAE advantage estimation and PPO clipped surrogate loss in `experiments/train_mappo.py`.
* **Findings & Key Results**:
  * GAT-MAPPO achieved a **6.0% collision rate** under severe joint physical network disruptions (a 94% safety improvement over baseline).
  * Saved trained model weights to `models/mappo_actor.pt`.

---

### Phase 6: Multi-Scenario Scaling & Mixed Autonomy

* **Timestamp**: 2026-09-01 00:43 IST
* **Milestone**: Intelligent Driver Model (IDM) Human Agents & Multi-Topology Benchmarks
* **Action Taken**:
  1. Implemented `src/agents/idm_human_agent.py` modeling non-communicative human drivers via the Intelligent Driver Model (Treiber et al., 2000).
  2. Implemented `spawn_roundabout_scenario` and `spawn_scalable_intersection` in `src/env/traffic_env.py`.
  3. Created `tests/test_mixed_autonomy.py` expanding test suite to 19 passing tests.
  4. Executed `experiments/run_mixed_autonomy_benchmarks.py` evaluating CAV penetration rates $\rho_{\text{CAV}} \in [0.0, 1.0]$ across Intersection, Highway Merge, and Roundabout scenarios.
* **Findings & Key Results**:
  * In high-speed highway merging, PET-Comm CAVs eliminated shockwave braking cascades at 50% CAV penetration, maintaining 0% collision rates.

---

### Phase 7: Systematic Sensitivity & Ablation Grid

* **Timestamp**: 2026-09-01 00:44 IST
* **Milestone**: Pareto Frontier Analysis & Channel Impairment Sweeps
* **Action Taken**:
  1. Built `experiments/run_sensitivity_ablation_grid.py` executing sweeps across error threshold $\epsilon$, latency $L$, packet loss $P_{\text{loss}}$, bandwidth limit $B$, and vehicle density $N$.
  2. Generated publication plots: `mixed_autonomy_benchmark.png`, `sensitivity_pareto_ablation.png`, and `density_scalability.png`.
* **Findings & Key Results**:
  * Pareto analysis revealed $\epsilon = 1.0\text{m}$ cuts message overhead by 68% while retaining robust trajectory tracking.
  * Recompiled `paper/main.pdf` including all multi-scenario and sensitivity figures with 0 build errors.

---

## Next Steps (Phase 8)

1. Finalize minor project presentation slide deck.
2. Polish live interactive visualization dashboard (`index.html`).
