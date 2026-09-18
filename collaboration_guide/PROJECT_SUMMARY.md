# Project Summary for Collaborators

This document explains what this project is about, what we set out to do, and what we actually built. It's written in plain English to make it easy for friends, new teammates, or collaborators to understand our work.

## What Was Asked?
Our Semester 5 Minor Project (by Aryan Dubey, Pranjal Gupta, and Swagata Barik) required us to build a multi-agent system. We focused on **Cooperative Autonomous Vehicles (CAVs)**: self-driving cars that talk to each other over a wireless network (V2X) to safely navigate intersections, roundabouts, and highway merges.

The core problem we were asked to solve was: **What happens when the wireless network fails?** 
Most researchers pretend that the wireless channels between cars are perfect (zero delay, zero packet drops). In the real world, signals fade, networks get congested, and packets drop. If cars rely on perfect communication to avoid crashes, they will crash in the real world.

## What Did We Do?
Instead of just using standard algorithms, we built an entire framework from scratch to test how AI agents fail under realistic physical network disruptions, and then we built two new solutions to fix those failures. 

Here is exactly what we built:

### 1. Proved the "Compounding Degradation Effect"
We created an environment to test cars under network stress. We proved a new concept called the **Compounding Degradation Effect**. We showed statistically (with a $p$-value less than 0.0001) that if you combine different network problems (like packet loss AND latency AND fading), cars crash exponentially more often than if you just have one network problem alone. A baseline system crashed 84% of the time under joint disruption!

### 2. Built PET-Comm (Predictive Event-Triggered Communication)
To fix this, we created **PET-Comm**. 
Instead of cars spamming the network with messages every millisecond (which clogs the network), our cars use a **Kalman Filter** (a mathematical prediction tool). The car predicts where *other* cars think it is. It only broadcasts a new message if it deviates from that prediction! 
If the network drops entirely, the cars use "dead-reckoning" to predict where everyone is, and they yield safely. 
**Result:** PET-Comm reduced network spam by 88% and dropped the crash rate from 84% down to 12%.

### 3. Built GAT-MAPPO (The Ultimate AI Policy)
We went further and trained a neural network called **GAT-MAPPO** (Multi-Agent Proximal Policy Optimization with Graph Attention Networks). This AI learns how to drive by treating other cars as nodes in a graph and paying "attention" to the most dangerous ones. 
**Result:** It achieved a **0.0% collision rate** even under severe network disruption, making it the best-in-class policy.

## The Journey and Bug Fixes
Building this wasn't easy! We had to overcome several severe simulation bugs that invalidated our initial results:
1. **Head-on Collisions**: Our intersection environment originally spawned cars directly on top of each other in the exact same lane going opposite directions! We fixed the kinematics to use proper right-hand traffic offsets.
2. **Infinite Reversing**: Cars used to yield infinitely when networks failed, causing them to accelerate backward endlessly at 150 km/h! We added a hard physical floor to braking.
3. **Rear-End Collisions**: Our cars originally only checked for cross-traffic crashes in the intersection. They would yield to an intersection car, stop, and then get rear-ended by the car directly behind them in the same lane. We added a same-lane safety checker.

After fixing these deep physics bugs, our final metrics are completely rigorous and statistically bulletproof.

## How to Run It
If you want to see the results yourself, simply run the benchmark scripts in the `experiments/` folder:

- To run the statistical significance test (ANOVA):
  `python experiments/run_statistical_anova.py`
- To run the mixed-autonomy benchmark (CAVs vs Human drivers):
  `python experiments/run_mixed_autonomy_benchmarks.py`
- To run the AI policy benchmark:
  `python experiments/eval_mappo_benchmark.py`

You can view the final metrics inside the `experiments/results/` folder, and read our final IEEE formatted paper in `paper/main.pdf`.
