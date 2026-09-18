# Communication-Aware Cooperative Agents

5th Semester Minor Project  
Dr. Shyama Prasad Mukherjee International Institute of Information Technology, Naya Raipur (IIIT Naya Raipur)

- **Supervisors**: Dr. Alaa Daoud, Prof. KG Srinivasa
- **Team Members**: Aryan Dubey, Pranjal Gupta, Swagata Barik
- **Original Presentation**: [Sem-5th minor.pdf](Sem-5th%20minor.pdf)

---

## 1. Project Background and Motivation

In cooperative intelligent transportation systems and Vehicle-to-Everything (V2X) networks, autonomous vehicles share state information (positions, velocities, headings, and intentions) to coordinate safely at unsignalized intersections, roundabouts, and highway merges.

Most existing multi-agent reinforcement learning (MARL) and communicative agent literature assumes ideal communication conditions or evaluates single disruptions in isolation (such as packet loss alone or latency alone), frequently on abstract toy grid worlds rather than realistic transportation coordination tasks.

In real-world vehicular environments, wireless communication channels face simultaneous, non-stationary disruptions:
- **Packet Loss**: Caused by obstacles, distance, interference, and multipath fading.
- **Latency / Delay**: Introduced by transmission delays, queuing, and hardware processing.
- **Bandwidth Constraints**: Caused by channel saturation and strict limits on message broadcast rates.

---

## 2. Research Problem and Gap

As identified in our project proposal literature review (referencing recent surveys and benchmarks including Liu et al. 2025, AgentComm-Bench 2026, TMC NeurIPS 2020, IntNet IEEE RA-L 2025, and ETCNet IEEE TNNLS 2023):

> **Core Research Gap**: No prior benchmark systematically evaluates cooperative multi-agent transportation coordination under **simultaneous, combined network disruptions** (joint packet loss, operational latency, and bandwidth constraints) using an interpretable, transparent agent architecture.

---

## 3. Research Questions and Core Hypotheses

### Primary Research Question (RQ1)
In a cooperative transportation coordination task, how does coordination performance and collision risk degrade under combined communication impairments (packet loss, latency, and bandwidth limits applied jointly) compared to each impairment tested in isolation?

- **Hypothesis**: Combined communication impairments degrade coordination performance **super-additively** (worse than the sum of their individual effects) because an agent's recovery strategy for one impairment (e.g., waiting for delayed messages) is severely compromised by simultaneous exposure to another (e.g., packet drop).

### Proposed Mitigation Concepts
1. **Idea 1: Predictive Event-Triggered Communication (PET-Comm)**
   - Agents maintain a local motion prediction model (such as a Kalman Filter or dead-reckoning) of neighboring vehicles' trajectories.
   - Communication is triggered only when an agent's actual state deviates beyond an error threshold from the predicted state.
   - In the event of packet drops, agents propagate predictions up to a safety deadline before initiating conservative fallback maneuvers.
2. **Idea 2: Criticality-Aware Reliable Retransmission (CARR)**
   - Emergency or high-severity events (such as hard braking or sudden lane deviations) require an explicit acknowledgment (ACK) handshake.
   - If an acknowledgment is dropped, retransmission is prioritized using dynamic backoff to eliminate catastrophic single-packet failure modes.

---

## 4. Current Stage: Implementation Options

We are currently at the initial stage of defining the exact scope and selecting the direction to implement. Full details on each pathway are documented in [PROJECT_OPTIONS.md](PROJECT_OPTIONS.md):

- **Option 1: Empirical Benchmark and Combined Degradation Study (RQ1 Focus)**  
  Focus on building the multi-agent traffic environment and communication impairment channel to rigorously prove or disprove the super-additive degradation hypothesis with clear metrics and plots.
- **Option 2: Predictive Event-Triggered Communication (PET-Comm)**  
  Focus on implementing local trajectory prediction models and adaptive event-triggering thresholds to demonstrate bandwidth reduction under lossy channels.
- **Option 3: Criticality-Aware Reliable Retransmission (CARR) Protocol**  
  Focus on a prioritized messaging transport layer with acknowledgment handshakes for safety-critical states.
- **Option 4: Comprehensive End-to-End Framework**  
  An integrated pathway covering the baseline benchmark (Option 1) followed by both mitigation strategies (Options 2 and 3).

---

## 5. Repository Layout and Working Branches

`	ext
agents-minor/
├── Sem-5th minor.pdf      # Original university proposal presentation
├── PROJECT_OPTIONS.md     # Detailed architectural options and roadmaps
├── README.md              # Project documentation and problem overview
├── requirements.txt       # Foundational Python dependencies
└── .gitignore             # Standard git ignore patterns
`

### Git Branches
- **main (Active)**: Clean, foundational starting stage of the project. Every file and line of code added here is built step-by-step with full student understanding.
- **ull-ai-project (Archive)**: A comprehensive, pre-generated prototype containing advanced MAPPO-GAT neural models, automated benchmark scripts, and manuscript drafts created during early exploratory iterations. Preserved for reference.

To inspect the archived prototype at any time:
`ash
git checkout full-ai-project
`
To return to the clean starting branch:
`ash
git checkout main
`

---

## 6. Getting Started

### Prerequisites
- Python 3.10 or higher
- Git

### Setup
`ash
# Clone the repository
git clone https://github.com/Pranjalstart679/agentic-minor.git
cd agentic-minor

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install basic dependencies
pip install -r requirements.txt
`
