---
name: v2x-experiment-runner
description: |
  Automated runner and statistical evaluation suite for V2X multi-agent communication experiments.
  Use this skill to execute Monte Carlo simulation sweeps, compute confidence intervals, run ANOVA & t-tests,
  and export publication-ready Matplotlib plots and JSON outputs.
---

# V2X Experiment Runner & Statistical Evaluation Skill

This skill provides reusable patterns for running rigorous multi-agent empirical experiments.

## Statistical Evaluation Methodology

When evaluating V2X multi-agent performance across experimental treatment groups:

1. **Monte Carlo Sampling**: Execute at least $N = 50$ independent simulation trials per condition using fixed, reproducible random seeds.
2. **Metrics Tracked**:
   - **Collision Rate**: $C = \frac{\text{Collisions}}{N_{\text{episodes}}}$
   - **Mean Velocity**: Average speed across active steps.
   - **Communication Load**: Total messages transmitted vs. delivered.
   - **Standard Error & 95% Confidence Interval**:
     $$\text{SE} = \frac{\sigma}{\sqrt{N}}, \quad \text{CI}_{95} = 1.96 \times \text{SE}$$
3. **Super-Additivity Hypothesis Test**:
   - Conduct **Welch's Independent Two-Sample T-Test** between joint combined impairment condition $f(L, P, B)$ and isolated impairment condition $f(L)$:
     $$t = \frac{\bar{X}_1 - \bar{X}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}}$$
   - Confirm hypothesis if $p < 0.05$ and mean collision rate of joint condition exceeds isolated sum.

## Directory & Artifact Outputs

- Experiment Scripts: `experiments/*.py`
- Output JSON Files: `experiments/results/*.json`
- Output Plot PNGs: `experiments/results/*.png`
- Web Dashboard Sync: `index.html`
