# Key Project Decisions & Conversation Highlights

This log captures essential conversation milestones, user directives, technical decisions, and empirical findings with timestamps.

---

## Chronological Highlights

### [2026-08-31 03:23 IST] Project Alignment & Scoping
* **Context**: User requested analysis of `Sem-5th minor.pdf` and implementation options.
* **Key Decision**: User chose **Option 4** (Comprehensive End-to-End Hybrid Framework combining baseline empirical degradation analysis with PET-Comm and CARR mitigation).
* **Artifact**: `PROJECT_OPTIONS.md`.

---

### [2026-08-31 03:32 - 03:36 IST] Core Architecture & Initial Empirical Tests
* **Key Actions**:
  * Initialized repository tree, `.venv`, `requirements.txt`, and unit test suite.
  * Implemented `comm_channel.py`, `traffic_env.py`, `kalman_filter.py`, `rule_agent.py`, `pet_comm_agent.py`, and `carr_agent.py`.
  * Verified all 9 unit tests passing.
* **Key Finding**: Baseline agents suffered 100% collision rate under combined physical impairments; PET-Comm reduced collisions down to 20%.
* **Artifact**: `TIMELINE.md`.

---

### [2026-08-31 03:40 IST] Statistical Hypothesis Testing & Rayleigh Fading
* **Context**: User requested making the project detailed, extensive, and deeply researched.
* **Key Actions**:
  * Implemented distance-dependent log-normal path loss and Rayleigh fading.
  * Added high-speed highway merge scenario.
  * Executed 50-trial Monte Carlo ANOVA suite (`run_statistical_anova.py`).
* **Key Finding**: Welch's $t$-test ($t = 2.585, p = 0.0128 < 0.05$) statistically confirmed the **Super-Additivity Hypothesis**.
* **Artifacts**: `PROJECT_ROADMAP.md`, `experiments/results/anova_super_additivity.png`.

---

### [2026-08-31 03:47 - 03:50 IST] Skills Creation & IEEE LaTeX Paper Setup
* **Context**: User directed to defer immediate publishing and focus on writing a high-quality base paper in LaTeX with good citations and creating reusable skills.
* **Key Actions**:
  * Created custom workspace skills in `.agents/skills/` (`communication-aware-marl` and `v2x-experiment-runner`).
  * Built `paper/references.bib` with citations for Liu 2025, AgentComm-Bench 2026, TMC 2020, IntNet 2025, ETCNet 2023, Kalman 1960, and Rappaport 2002.
  * Created `paper/main.tex` and compiled `paper/main.pdf` using MiKTeX `pdflatex` and `bibtex`.

---

### [2026-08-31 03:55 IST] Phase 5: Deep MARL (MAPPO + GAT) Implementation
* **Context**: User approved roadmaps and directed execution of Phase 5.
* **Key Actions**:
  * Implemented `GraphAttentionLayer` and `MAPPOActor` / `MAPPOCritic` architectures.
  * Built PyTorch Actor-Critic PPO training loop with GAE and entropy regularization.
  * Expanded test suite to 13 unit tests (100% pass rate).
* **Key Finding**: MAPPO Deep RL achieved a **6.0% collision rate** under severe joint physical network disruptions (a 94% safety improvement over baseline).
* **Artifacts**: `models/mappo_actor.pt`, `paper/main.pdf`, `index.html`.

---

### [2026-08-31 04:05 IST] System Audit & Training Bottleneck Analysis
* **Context**: User requested codebase review and training duration breakdown.
* **Key Resolution**: Full audit completed and computational bottlenecks analyzed.
* **Artifact**: `reports/AUDIT_AND_TRAINING_ANALYSIS.md`.
