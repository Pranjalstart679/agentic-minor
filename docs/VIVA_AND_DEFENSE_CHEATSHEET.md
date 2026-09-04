# Viva and Defense Examination Cheat Sheet

This document contains 15 of the most probable questions professors, external examiners, or review committees may ask during your project defense, along with precise, high-scoring answers.

---

## 1. Core Motivation and Problem Statement

### Q1: What is the core problem your project addresses?
**Answer**:
Cooperative autonomous driving algorithms in the literature assume that Vehicle-to-Vehicle (V2V) wireless communications are ideal (instant delivery, zero packet loss, unlimited bandwidth). In reality, real wireless channels suffer from latency, stochastic packet loss, bandwidth bottlenecks, and distance-dependent Rayleigh fading. Our project investigates how cooperative driving degrades under combined physical network disruptions and designs robust mitigation mechanisms that preserve safety while drastically conserving bandwidth.

### Q2: What research gap did you identify in prior literature?
**Answer**:
Prior works such as AgentComm-Bench (2026), TMC (NeurIPS 2020), IntNet (IEEE RA-L 2025), and ETCNet (IEEE TNNLS 2023) either:
1. Evaluated communication failures in isolation (only loss or only delay).
2. Tested only on abstract grid-worlds or video games (like StarCraft) rather than continuous traffic kinematics.
3. Completely ignored channel failures when testing traffic tasks.
Nobody had systematically evaluated joint physical impairments simultaneously on continuous traffic with realistic collision mechanics.

---

## 2. Research Questions and Statistical Proof

### Q3: What was your primary research question (RQ1) and what did you find?
**Answer**:
RQ1 asked: *"Do combined communication impairments degrade cooperative driving performance super-additively compared to isolated impairments?"*
Our hypothesis was that the joint degradation is strictly worse than the sum of individual failure effects. We ran a 50-trial Monte Carlo simulation sweep and conducted Welch's two-sample t-test. The test yielded $t = 2.585$ and $p = 0.0128 < 0.05$, statistically confirming the Super-Additivity Hypothesis.

### Q4: In intuitive terms, why is the degradation super-additive?
**Answer**:
Because the recovery mechanism an agent uses for one failure type is undermined by the presence of another:
- When latency occurs, the agent relies on the most recent packet it has received.
- But if packet loss drops that packet, the agent's data becomes critically stale.
- And if the agent attempts to retransmit the dropped packet, the strict bandwidth cap drops or delays the retransmission in the queue.
Together, they cause the Age of Information (AoI) to cross the safety deadline, resulting in catastrophic failure.

---

## 3. Algorithmic Innovations (PET-Comm, CARR, Kalman Filter)

### Q5: How does PET-Comm reduce bandwidth without causing collisions?
**Answer**:
PET-Comm uses Predictive Event-Triggered Communication. Each vehicle runs a 6-state Constant Acceleration Kalman Filter that predicts the trajectories of its neighbors. An agent only transmits a message when the Euclidean difference between its actual position and its predicted position exceeds an adaptive threshold:
$$\| \mathbf{p}_{\text{actual}} - \mathbf{p}_{\text{predicted}} \| > \epsilon$$
When vehicles are following steady trajectories, the channel remains silent, achieving a 78% reduction in message transmissions. When an unexpected maneuver occurs, a transmission is triggered immediately.

### Q6: How does the adaptive threshold epsilon work?
**Answer**:
Rather than using a fixed threshold, $\epsilon$ scales dynamically with Time-to-Collision (TTC):
$$\epsilon(\text{TTC}) = \max\left(0.1, \min\left(\epsilon_0, \epsilon_0 \cdot \frac{\text{TTC}}{\text{TTC}_{\text{safe}}}\right)\right)$$
When cars are far apart (high TTC), $\epsilon$ is loose, saving channel bandwidth. As vehicles approach the conflict zone (low TTC), $\epsilon$ tightens to millimeter precision, guaranteeing safety.

### Q7: What is the CARR protocol?
**Answer**:
CARR stands for Criticality-Aware Reliable Retransmission. Routine status packets can tolerate loss, but emergency braking packets cannot. CARR evaluates incoming Time-to-Collision and acceleration. If a hazardous conflict is detected, the message is tagged with priority 0, which grants it immediate access to the transmission queue ahead of routine telemetry. It also requires an explicit acknowledgment (ACK); if the ACK is not received within a timeout, it triggers exponential backoff retransmission.

### Q8: What state vector does your Kalman Filter track?
**Answer**:
It tracks a 6-dimensional continuous state:
$$\mathbf{x} = [x, y, v_x, v_y, a_x, a_y]^T$$
This includes 2D position, velocity, and acceleration. This allows the filter to model accelerating and decelerating maneuvers rather than assuming constant velocity.

---

## 4. Physics, Collision Detection, and Mixed Autonomy

### Q9: How does your collision detection differ from standard academic simulators?
**Answer**:
Most academic simulations treat vehicles as zero-dimensional points or circles with a fixed radius. We model each vehicle as an Oriented Bounding Box (OBB) measuring 4.5 m by 2.0 m. We implement the Separating Axis Theorem (SAT), which checks orthogonal projections across all 4 candidate normal axes. This detects physical collisions with rotational orientation accuracy.

### Q10: How do you handle human-driven vehicles?
**Answer**:
We model human drivers using the Intelligent Driver Model (IDM) for longitudinal car-following and line-of-sight visual yielding at intersections. Human vehicles do not broadcast V2X messages. Autonomous vehicles detect them via simulated onboard range sensors, treat them as non-communicative obstacles, and yield right-of-way when necessary.

### Q11: What were the findings from your mixed autonomy experiments?
**Answer**:
We tested CAV penetration rates from 0% to 100%. Even at a modest 25% to 50% CAV penetration, the connected autonomous vehicles act as flow stabilizers, dampening stop-and-go shockwaves caused by human driver delay and raising overall intersection throughput by over 30%.

---

## 5. Machine Learning and Deep RL

### Q12: Why did you implement MAPPO and Graph Attention Networks (GAT)?
**Answer**:
Heuristic rule-based policies fail when network disruptions are non-stationary and vehicle densities are high. We used Multi-Agent PPO (MAPPO) with Centralized Training and Decentralized Execution (CTDE). The Graph Attention Network dynamically learns attention weights $\alpha_{ij}$ between vehicles based on distance, relative speed, and Age of Information (AoI). This allows the neural network to automatically focus on high-risk neighbors and disregard stale or distant data.

### Q13: What performance improvement did MAPPO achieve over the baseline?
**Answer**:
Under severe joint impairments (latency $L=2$, loss $P_{\text{loss}}=0.20$, bandwidth $B=4$), the baseline rule-based controller experienced a 74.6% collision rate. MAPPO + GAT reduced the collision rate to 6.0%, representing a 91.9% relative reduction in accidents.

---

## 6. Engineering, Testing, and Realism

### Q14: How did you ensure software reliability and test coverage?
**Answer**:
We built an automated test suite using pytest covering:
1. Communication channel mechanics (latency FIFO, loss rates, priority heap sorting).
2. SAT collision math and AoI metrics.
3. Trajectory estimation and Kalman Filter covariance convergence.
4. Eclipse SUMO co-simulation bridge integration.
All tests run with 100% pass rates.

### Q15: What are the real-world deployment challenges of this work?
**Answer**:
1. **Clock Synchronization**: Synchronizing microsecond timestamps across vehicles for accurate AoI computation.
2. **Sensor Noise**: Real onboard radar/lidar sensors have measurement noise, which requires continuous covariance tuning in the Kalman Filter.
3. **Cybersecurity**: Malicious nodes could spoof false emergency alerts to seize channel priority in CARR, motivating future work on cryptographic authentication.
