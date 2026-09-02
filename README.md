# Communication-Aware Cooperative Agents

A multi-agent framework to evaluate and optimize cooperative autonomous agent behavior under non-stationary physical communication impairments (latency, packet loss, and bandwidth constraints).

## Overview

In Vehicle-to-Everything (V2X) and cooperative multi-agent systems, agents rely on real-time state and trajectory sharing to coordinate safely (e.g. unsignalized intersections, highway lane merging). However, real-world wireless communication introduces disruptions:
- Latency (transmission and processing delays)
- Packet Loss (channel noise, fading, collision of frames)
- Bandwidth Limits (network capacity caps)

This repository provides a modular simulation environment and communication channel to systematically benchmark isolated versus combined communication failures (RQ1), alongside two core mitigation strategies:
1. **Predictive Event-Triggered Communication (PET-Comm)**: Trajectory prediction (Kalman filtering / dead-reckoning) to send messages only when state deviates beyond threshold $\epsilon$.
2. **Criticality-Aware Reliable Retransmission (CARR)**: Priority-based transport protocol with reliable ACK retransmission for emergency events.

## Repository Structure

```text
agents-minor/
├── Sem-5th minor.pdf          # Semester 5 minor project presentation deck
├── PROJECT_OPTIONS.md        # Technical proposal & options breakdown
├── TIMELINE.md               # Timestamped project activity & decision log
├── requirements.txt          # Python dependencies
├── src/
│   ├── env/                  # Traffic environment & communication channel models
│   ├── agents/               # Baseline, PET-Comm, and CARR agent controllers
│   ├── estimation/           # Kalman Filter and motion predictors
│   └── utils/                # Evaluation metrics and plotting utilities
├── experiments/              # Scripts to run RQ1 benchmark & mitigation tests
└── tests/                    # Unit & integration tests
```

## Setup & Quickstart

```bash
# Create and activate Python virtual environment
python -m venv .venv
.venv\Scripts\activate   # On Windows (pwsh / cmd)

# Install dependencies
pip install -r requirements.txt

# Run unit tests
python -m pytest tests/
```

## Project Documentation & Timeline

- Project Implementation Options: [PROJECT_OPTIONS.md](PROJECT_OPTIONS.md)
- Activity & Timeline Log: [TIMELINE.md](TIMELINE.md)
