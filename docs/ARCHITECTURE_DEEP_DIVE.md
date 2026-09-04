# Architecture Deep Dive: Algorithms, Models, and Mathematics

This document provides a thorough technical breakdown of the mathematics, algorithms, and data structures implemented in the Communication-Aware Multi-Agent V2X framework.

---

## 1. Physical Simulation and Kinematics (`src/env/traffic_env.py`)

### 1.1 Continuous Kinematics
Each vehicle $i$ is governed by continuous 2D planar kinematics with a discrete simulation timestep $\Delta t = 0.1\text{ s}$:

```text
x_i(t + dt) = x_i(t) + v_{x,i}(t) * dt + 0.5 * a_{x,i}(t) * dt^2
y_i(t + dt) = y_i(t) + v_{y,i}(t) * dt + 0.5 * a_{y,i}(t) * dt^2
v_i(t + dt) = max(0, v_i(t) + a_i(t) * dt)
```

Where:
- Control actions are longitudinal accelerations: $a_i \in [a_{\min}, a_{\max}] = [-6.0, 3.0]\text{ m/s}^2$.
- Maximum speed is capped at $v_{\max} = 15.0\text{ m/s}$ (~54 km/h).

### 1.2 Oriented Bounding Box (OBB) and Separating Axis Theorem (SAT)
Rather than abstracting vehicles as zero-dimensional points or circles, vehicles are modeled as physical rectangular bounding boxes of length $L = 4.5\text{ m}$ and width $W = 2.0\text{ m}$.

Collision detection evaluates whether two convex polygons intersect using the **Separating Axis Theorem**:
Two oriented rectangles do not intersect if and only if there exists a 1D projection axis along which their orthogonal projections are completely disjoint.

For two rectangles $A$ and $B$, the set of candidate separating axes $\mathcal{A}$ consists of the normals to the edges of both boxes (4 candidate axes in total):
```text
Candidates = { n_{A,1}, n_{A,2}, n_{B,1}, n_{B,2} }
```
For each axis $\mathbf{n} \in \mathcal{A}$:
```text
proj_A = [ min_{p \in V_A} (p · n),  max_{p \in V_A} (p · n) ]
proj_B = [ min_{p \in V_B} (p · n),  max_{p \in V_B} (p · n) ]
```
If for any axis $\max(\text{proj}_A) < \min(\text{proj}_B)$ or $\max(\text{proj}_B) < \min(\text{proj}_A)$, a separating axis is found, guaranteeing that the vehicles have not collided. If no separating axis exists across all 4 candidate normals, a physical collision is registered.

### 1.3 Age of Information (AoI)
The freshness of received information from neighboring vehicle $j$ available at vehicle $i$ is tracked continuously:
```text
AoI_{i,j}(t) = t - \tau_{i,j}^{\text{last}}
```
Where $\tau_{i,j}^{\text{last}}$ is the generation timestamp of the most recently received packet from vehicle $j$. In ideal networks, $\text{AoI} = \Delta t$. Under latency $L$ and packet loss, AoI grows monotonically, serving as a critical safety metric for cooperative agents.

---

## 2. Wireless Channel Impairment Model (`src/env/comm_channel.py`)

The wireless medium injects four physical network constraints:

### 2.1 Latency
Messages are pushed into a discrete FIFO queue with delay $L$:
```text
packet.deliver_time = t + L
```
Packets remain inaccessible to neighboring vehicles until $t \ge \text{deliver\_time}$.

### 2.2 Packet Loss
Packet loss occurs stochastically via Bernoulli trial:
```text
P(drop) = p_{\text{loss}}
```
When a packet drops, it is removed from the transmission queue and never reaches receivers.

### 2.3 Bandwidth Limiting (Min-Heap Priority Queue)
If $N_{\text{msgs}} > B_{\max}$ (the maximum bandwidth limit per timestep), packets compete for channel access. High-priority messages (e.g. CARR critical emergency alerts) are ordered before routine telemetry using a min-heap comparator:
```text
Key = (priority_level, creation_time)
```
The top $B_{\max}$ messages are transmitted; excess messages exceeding the buffer limit are dropped.

### 2.4 Rayleigh Fading and Distance-Dependent Path Loss
Signal power decays with physical distance $d = \|\mathbf{p}_i - \mathbf{p}_j\|$ according to the log-distance path loss model:
```text
gamma(d) = gamma_bar * (d / d_0)^(-alpha)
```
Where:
- $\alpha = 2.8$ is the path loss exponent (urban vehicular environment).
- $d_0 = 1.0\text{ m}$ is the reference distance.
- $\bar{\gamma} = 25.0\text{ dB}$ is the reference signal-to-noise ratio (SNR).

Multipath interference is modeled using Rayleigh fading, leading to an exponential SNR distribution. The probability of packet decoding failure at distance $d$ is:
```text
P_loss(d) = 1 - exp( - gamma_th / gamma(d) )
```
Where $\gamma_{\text{th}} = 5.0\text{ dB}$ is the receiver sensitivity threshold.

---

## 3. Kinematic Estimation: 6-State Kalman Filter (`src/estimation/kalman_filter.py`)

To bridge communication gaps caused by packet loss and latency, each agent runs a local continuous Kalman Filter for each neighbor.

### 3.1 State Representation
The state vector tracks position, velocity, and acceleration in 2D Cartesian space:
```text
x = [p_x, p_y, v_x, v_y, a_x, a_y]^T
```

### 3.2 State Transition Model
Using the constant acceleration kinematic model over timestep $\Delta t$:
```text
x_{t+1} = F * x_t + w_t,    w_t ~ N(0, Q)
```
Where the state transition matrix $F$ is:
```text
F = [ 1  0  dt  0  0.5*dt^2       0     ]
    [ 0  1   0 dt     0        0.5*dt^2 ]
    [ 0  0   1  0    dt           0     ]
    [ 0  0   0  1     0          dt     ]
    [ 0  0   0  0     1           0     ]
    [ 0  0   0  0     0           1     ]
```

### 3.3 Predict and Update Steps
- **Prediction Step** (run every timestep regardless of message arrival):
  ```text
  x̂_{t|t-1} = F * x̂_{t-1|t-1}
  P_{t|t-1} = F * P_{t-1|t-1} * F^T + Q
  ```
- **Measurement Update Step** (executed only when a packet arrives):
  ```text
  y_t = z_t - H * x̂_{t|t-1}
  S_t = H * P_{t|t-1} * H^T + R
  K_t = P_{t|t-1} * H^T * S_t^(-1}
  x̂_{t|t} = x̂_{t|t-1} + K_t * y_t
  P_{t|t} = (I - K_t * H) * P_{t|t-1}
  ```
When communication is severed, the agent continues executing the prediction step, maintaining an accurate estimate of neighboring trajectories for up to $T_{\text{safe}} = 1.5\text{ seconds}$.

---

## 4. Mitigation Protocols

### 4.1 PET-Comm: Predictive Event-Triggered Communication (`src/agents/pet_comm_agent.py`)
Standard cooperative vehicles broadcast messages periodically (e.g. 10 Hz), flooding the channel.

In PET-Comm:
1. Each vehicle maintains a twin of its neighbor's Kalman Filter, predicting what the world thinks this vehicle is doing.
2. At timestep $t$, the vehicle computes the prediction error:
   ```text
   e_t = || p_actual(t) - p_predicted(t) ||
   ```
3. Transmission condition:
   ```text
   Transmit packet if and only if e_t > epsilon
   ```
4. **Adaptive Threshold**: $\epsilon$ scales dynamically with approaching conflict risk:
   ```text
   epsilon(TTC) = max(0.1, min(epsilon_0, epsilon_0 * (TTC / TTC_safe)))
   ```
   When vehicles are far apart, $\epsilon$ is large (transmitting few updates). As vehicles enter conflicting trajectories (low TTC), $\epsilon$ tightens, providing millimeter precision.

### 4.2 CARR: Criticality-Aware Reliable Retransmission (`src/agents/carr_agent.py`)
Routine telemetry packets tolerate small loss rates, but emergency braking packets cannot be dropped.

1. **Severity Classification**:
   ```text
   Severity = CRITICAL if (TTC < 2.0 s and a_i < -2.0 m/s^2) else ROUTINE
   ```
2. **Priority Injection**: Critical packets enter the channel with priority 0 (highest priority), bypassing routine packets in the min-heap bandwidth queue.
3. **Explicit ACK Handshake**:
   - Receiver sends back an acknowledgment packet upon reception.
   - If the sender does not receive an ACK within timeout $\tau_{\text{ack}} = 2\Delta t$, it triggers an immediate retransmission with exponential backoff:
     ```text
     timeout_{k+1} = timeout_k * 1.5
     ```

---

## 5. Mixed Autonomy: Intelligent Driver Model (`src/agents/idm_human_agent.py`)

To evaluate real-world mixed traffic where not all vehicles are autonomous or communicative, human drivers are simulated via the **Intelligent Driver Model (IDM)**:

### 5.1 Car-Following Acceleration
```text
a_IDM = a_max * [ 1 - (v / v_0)^delta - (s*(v, delta_v) / s)^2 ]
```
Where:
- $v_0$ is the desired free-flow velocity (12.0 m/s).
- $\delta = 4$ is the acceleration exponent.
- $s$ is the actual net bumper-to-bumper distance to the leading vehicle.
- $s^*(v, \Delta v)$ is the dynamic desired minimum headway:
  ```text
  s*(v, delta_v) = s_0 + max(0, v * T_gap + (v * delta_v) / (2 * sqrt(a_max * b_comf)))
  ```
  - $s_0 = 2.0\text{ m}$ (jam distance).
  - $T_{\text{gap}} = 1.2\text{ s}$ (safe time headway).
  - $b_{\text{comf}} = 2.0\text{ m/s}^2$ (comfortable deceleration).

### 5.2 Line-of-Sight Intersection Yielding
Human vehicles do not use V2X radio. Instead, they scan their 90-degree front visual field within a sight distance of $d_{\text{sight}} = 35.0\text{ m}$. If another car occupies the intersection zone with a smaller expected time-to-arrival, the human driver decelerates safely.

---

## 6. Deep MARL: MAPPO with Graph Attention Networks (`src/agents/mappo_agent.py`, `src/agents/gat_layer.py`)

When rule-based heuristics encounter extreme network noise and high traffic densities, learned neural policies provide superior robustness.

### 6.1 Centralized Training with Decentralized Execution (CTDE)
- **Centralized Critic**: Takes global environment state (all vehicle true coordinates, velocities, and channel states) to accurately estimate the state-value function $V_\phi(s)$.
- **Decentralized Actor**: Each vehicle $i$ inputs only its local observation and received communication buffer:
  ```text
  o_i = [ x_i, y_i, v_i, a_i, d_goal, { x̂_j, v̂_j, AoI_{i,j} }_{j \in N_i} ]
  ```

### 6.2 Graph Attention Network (GAT) Formulation
Vehicles are modeled as nodes in a dynamic graph whose edge weights correspond to communication reception.
For vehicle $i$ and neighbor $j$:
```text
e_{ij} = LeakyReLU( a^T * [ W * h_i || W * h_j || W_aoi * AoI_{ij} ] )
alpha_{ij} = softmax_j( e_{ij} ) = exp(e_{ij}) / sum_{k \in N_i} exp(e_{ik})
```
The updated vehicle embedding aggregates neighbor features weighted by their criticality and data staleness:
```text
h_i' = sigma( sum_{j \in N_i} alpha_{ij} * W * h_j )
```
This enables the vehicle to automatically down-weight stale information and prioritize neighbors with dangerous trajectories.

### 6.3 PPO Clipped Surrogate Objective
The actor policy $\pi_\theta$ is updated using the clipped surrogate objective with Generalized Advantage Estimation (GAE):
```text
L^CLIP(theta) = E [ min( r_t(theta) * A_t,  clip(r_t(theta), 1 - eps, 1 + eps) * A_t ) ]
```
Where:
```text
r_t(theta) = pi_theta(a_t | o_t) / pi_{theta_old}(a_t | o_t)
```
An entropy regularization term $H(\pi_\theta)$ encourages exploratory maneuvering during training.
