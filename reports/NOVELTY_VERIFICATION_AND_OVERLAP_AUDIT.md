# Novelty Verification & Related-Work Overlap Audit

**Revision 2** — 2026-09-04 (supersedes rev 1, same date)
**Scope**: every entry in `paper/references.bib`; the differentiation matrix and five contributions in `docs/NOVELTY_AND_CONTRIBUTIONS.md`; `paper/main.tex`; every file in `experiments/results/`; the agent and environment sources they were produced by.
**Method**: each citation looked up against arXiv, OpenAlex, IEEE Xplore metadata and the NeurIPS proceedings. Overlap candidates found by topical search per contribution. Result JSONs read directly and compared line-by-line against the numbers printed in prose. Code read to explain the numbers rather than to trust them.

---

## 1. What changed since revision 1

Rev 1 raised three problems: fabricated citation metadata, two inverted research-gap claims, and a metrics table that contradicted the repo's own data. **The first two are now closed.** The third is partly closed and has been traced to root causes in code.

| Rev 1 finding | Status |
| :--- | :--- |
| 5 of 12 references had invented authors/titles/venues | **Fixed.** All 12 entries in `references.bib` verify against primary sources. |
| `paper/main.md` carried the full fabricated reference list | **Fixed** by deleting the file. `main.tex` + `references.bib` are now the single source. |
| "90%+ of MARL papers assume ideal comms" — statistic does not exist | **Fixed.** Removed repo-wide. |
| AgentComm-Bench described as grid-world token noise | **Fixed.** Now "synthetic application-layer faults / cooperative embodied AI / joint application faults". |
| TMC described as having no packet loss | **Fixed.** Now "Temporal Message Control / loss robustness via buffering". |
| DCT-MARL cited but absent from both comparison tables | **Fixed.** Added to `NOVELTY §2` and `main.tex` Table I, with the 1-D-platoon delta stated. |
| IntNet asserted to assume a perfect channel (unverifiable) | **Fixed.** Softened to "does not evaluate fading channel loss". |
| "first / first-of-its-kind / first end-to-end integration" | **Fixed.** All removed; §1 now claims integration, not primacy. |
| `Control_Ideal` collision rate of 0.88 invalidated all of RQ1 | **Fixed.** Now 0.04. See §2.1 — the result is now genuinely strong. |
| ε = 1.0 m "Pareto optimal" point not present in the data | **Fixed.** Claim removed. |
| "300% worse than the sum of isolated failures" | **Fixed.** Removed. |
| Selective reporting of the significant t-test over the non-significant ANOVA | **Fixed.** Both now reported, and both are now significant. |
| Mixed-autonomy 0.0%-at-50% cherry-pick | **Fixed, and better.** §3 now reports the roundabout regression and the highway-merge null result explicitly. |
| Stale `t = 2.585 / p = 0.0128 / ANOVA p = 0.0676 / F = 2.417` | **Fixed** in `.md`, `.tex` and `.html` — zero occurrences remain. |
| Message-volume column inverted | **Fixed** in `NOVELTY §4` and `main.tex` (612.2 / 480.9 / 68.9 / 1428.0 all match the JSON). |
| PET-Comm mean speed of 40–51 m/s | **Root cause found and changed** — but the failure mode inverted rather than resolved. See §4.1. |
| Mean-speed column matches no result file | **Open.** Still stale in four files. See §4.2. |

The honesty of `docs/NOVELTY_AND_CONTRIBUTIONS.md` §3 is now the strongest part of the document. Reporting the freezing-robot trade-off, the roundabout regression at ρ=0.5/0.75, and PET-Comm's null result on highway merging is exactly the right call: those are findings, and a reviewer who finds them stated up front reads the rest of the paper in good faith.

What follows is the residual: seven open defects, four things that are missing rather than wrong, a prioritised next-step list, and four directions that would convert this from a solid systems study into a contribution with a mechanism behind it.

---

## 2. Citation record — closed

Retained as the verification record. Every entry below was checked against a primary source and now matches `paper/references.bib`.

| Key | Verified against |
| :--- | :--- |
| `liu2025robust` | arXiv:2511.11393, 14 Nov 2025. Liu Zejiao + 8. Preprint, **no journal** — do not cite as TPAMI. Its claim is qualitative ("most existing approaches assume communication is instantaneous, reliable, unlimited"), never a percentage. |
| `bansal2026agentcomm` | arXiv:2603.20285, 18 Mar 2026. Bansal Aayam, Gangwani Ishaan. Preprint, no venue. |
| `zhang2020tmc` | NeurIPS 33 (2020). Zhang Sai Qian, Zhang Qi, Lin Jieyu. **Temporal** Message Control. |
| `parada2025intnet` | IEEE RA-L 10(3):2478–2485, DOI 10.1109/LRA.2025.3531146, 17 Jan 2025. Parada Leandro, Yu Kevin, Angeloudis Panagiotis. |
| `hu2023etcnet` | IEEE TNNLS 34(8):3966–3978, DOI 10.1109/TNNLS.2021.3121546. Hu Guangzheng, Zhu Yuanheng, Zhao Dongbin, Zhao Mengchen, Hao Jianye. |
| `xu2025dctmarl` | arXiv:2508.12633. Xu Yaqi, Shi Yan, Tian Jin, Xia Fanzeng, Li Tongxin, Chen Shanzhi, Ge Yuming. |
| `kalman1960new`, `rappaport2002wireless`, `treiber2000congested`, `sutton2018reinforcement`, `kaul2012real`, `dresner2008multiagent` | All correct (Dresner pages now 591–656). |

**One residual claim still rests on an unread source.** `main.tex:71` says IntNet "does not evaluate fading channel loss". The Imperial preprint PDF has compressed text streams and the RA-L version is closed-access, so its channel model was never read. The softened wording is defensible; a confirming read is still owed before submission, because the paper is titled *"A Communication-Driven … Framework"* and a reviewer from that group would check.

### 2.1 The repaired RQ1 result is stronger than the paper claims

`experiments/results/anova_results.json` (regenerated, mtime after HEAD):

| Condition | Mean collision rate | Excess over control |
| :--- | :--- | :--- |
| `Control_Ideal` | 0.04 | — |
| `Iso_Latency` | 0.30 | **+0.26** |
| `Iso_Loss` | 0.04 | **+0.00** |
| `Joint_Combined` | 0.72 | **+0.68** |

Welch's t: `4.5826`, `p = 1.355e-05`. One-way ANOVA: `F = 41.35`, `p = 9.50e-21`. Joint excess is **2.6×** the sum of isolated excesses. This is no longer a ceiling artifact and no longer needs hedging.

It also supports a sharper claim than the one being made. `Iso_Loss` is *identical* to the control — 0.04, same standard error. **Packet loss alone is free; latency alone costs 26 points; together they cost 68.** "Impairments compound" undersells that. The finding is that loss is harmless until latency removes the slack the retransmission process needs, at which point it becomes the dominant term — a genuine interaction with a mechanism, not a monotone worsening. `docs/EXPERIMENTS_AND_RESULTS.md` §1.4 still explains the old 88/88/94/100 data and should be rewritten around this instead. §7.1 below turns it into a closed-form prediction.

---

## 3. Overlapping prior work, by contribution

Unchanged from rev 1 except where marked. This section is the reason the "first" language had to go; it is also where the defensible residual claims live.

### 3.1 Joint / compound disruptions (Contribution 1)

- **AgentComm-Bench** (arXiv:2603.20285) — six impairment dimensions jointly: latency, loss, bandwidth collapse, async updates, stale memory, conflicting evidence. Its closing recommendation is *report across multiple impairment settings rather than one idealised one* — the same argument as RQ1, five months earlier.
- **DCT-MARL** (arXiv:2508.12633) — non-ideal V2V channel + MARL + vehicle control; delay handled by state augmentation, loss by multi-key topology gating. Closest prior work to the whole premise.
- **Reason-to-Transmit** (arXiv:2603.20308) — bandwidth budget + up to 50% loss for cooperative perception.
- **Liu et al. survey** (arXiv:2511.11393) §III–IV — catalogues per-axis work (VFFAC, CoDe's DT-Dec-POMDP, DACOM). Evidence each axis is studied; not evidence the joint case is untouched.

**Defensible residual:** the impairments are *causally coupled through one physical channel* — distance drives loss, loss drives queue backlog, backlog drives latency — rather than being three independent injected knobs. Rev 1 recommended making this the claim; `main.tex:48` now says "causally coupled", which is the right move. §7.1 is what makes it rigorous.

### 3.2 Physical wireless layer + continuous kinematics (Contribution 2)

"Prior art used uniform RNGs detached from agent position" holds for the MARL-communication literature but not for MARL-for-V2X, which routinely models channels in *more* detail than η=2.7 + Rayleigh: platoon C-V2X channel assignment and power allocation (arXiv:2011.04555), the C-V2X radio-resource-allocation benchmark (arXiv:2603.06607), cognitive-V2X QTRAN with Manhattan mobility and co-channel interference (Appl. Sci. 16(12):6188), and joint learning/communication MARL over a real noisy channel (Imperial IPC-Lab).

**Defensible residual:** the *objective*. Those papers optimise the radio and treat driving as mobility input; this one optimises driving safety and treats the radio as a disturbance. Narrower and more honest than "first end-to-end integration".

### 3.3 PET-Comm (Contribution 3) — most exposed to a "not novel" review

Every component has direct prior art: **TMC** (NeurIPS 2020) transmits only when the new message exceeds a Euclidean threshold from the last sent one, with loss-tolerant receiver buffering — structurally the same trigger; **ETCNet** (TNNLS 2023) derives the trigger threshold from the bandwidth budget; **Model-Based Communication** (Nourkhiz Mahjoub, Toghi, Gani, Fallah; arXiv:1903.01576, 2019) shares a *model* instead of samples so the receiver tracks the remote agent — PET-Comm's idea with a Gaussian Process in place of a Kalman filter, from 2019; **ETSI ITS CAM/VAM generation rules** already trigger on dynamics deltas, so event-triggered V2X is normative, not novel; **Age of Information** (Kaul 2012, already in the bib) is the theory of when an update is worth sending; **arXiv:2605.10482** does event-triggering plus learned priority scheduling.

**Defensible residual:** the *fallback ladder* — dead-reckon on the Kalman prediction to `T_safe`, then degrade to conservative yield-braking — evaluated on collision rate rather than tracking error or bandwidth. Claim the ladder, not the trigger. Note that the ladder is also what produces the freezing-robot failure (§4.1), so §7.3 is the natural completion of this contribution.

### 3.4 Mixed autonomy, IDM humans, penetration sweep (Contribution 4)

IDM for HDVs and sweeping ρ_CAV is standard practice, not a contribution. The phase-transition finding is also already published: **arXiv:2608.09987** reports "a convex relationship between CAV penetration and system efficiency, identifying a critical instability regime at intermediate penetration rates (approximately 45%)" — the same claim with a mechanism, at nearly the same penetration. See also arXiv:1803.05577, arXiv:2401.11148, arXiv:2411.10031, arXiv:2606.20648.

**Defensible residual:** the same sweep run *under channel disruption* across three topologies, and — newly, per the honest rewrite — the finding that a conservative event-triggered protocol can be *worse* than broadcast in continuous-flow topologies. Nobody in the list above degrades the channel, and nobody reports a protocol regression.

### 3.5 GAT-MAPPO (Contribution 5) — open question from rev 1 now answered, negatively

Prior art: **IntNet** (RA-L 10(3), 2025) — graph attention over received messages plus a scheduler trimming the graph, up to 60% comm reduction, for cooperative driving; **arXiv:2007.02794** — CAV graph + attention on car-following *and unsignalised intersections* in mixed autonomy; **arXiv:2506.00982** — MARL + V2V to hardware; **DCT-MARL** — runtime topology adaptation keyed on live link status.

Rev 1 flagged one possible residual — "attention conditioned on channel state, *if* that is what the implementation does" — and said to check `src/agents/gat_layer.py` first. **It is not what the implementation does.** `gat_layer.py:48-54` computes `e_ij = LeakyReLU(aᵀ[Wh_i ‖ Wh_j])` and softmaxes over neighbours. The attention input contains state features only; the layer has no access to link reliability, delivery ratio, AoI, or path loss. It is a textbook Veličković GAT.

So as implemented, Contribution 5 has **no architectural novelty over IntNet** — the comparison table's own "IntNet-like" concession is accurate. What it has is an evaluation novelty: the same architecture measured under a physical channel. That is publishable but thin. §7.2 is the change that would make it a real contribution, and it is small.

---

## 4. Open defects

### 4.1 PET-Comm is deadlocked, not conservative

`mappo_eval_results.json` → `PET_Comm.avg_speed = 0.6129 m/s` (2.2 km/h). Two lines in the current agent diff cause it:

```python
same_lane = (self_state.x*nx + self_state.y*ny) > 0 and abs(atan2(...) - atan2(...)) < 0.2
if same_lane and self_dist > n_dist and (self_dist - n_dist) < 20.0:
    should_yield = True                      # no gap-safety test
...
action_accel = self.max_decel if self_speed > 0.5 else 0.0   # stopped stays stopped
```

The `same_lane` rule makes any follower within 20 m yield to its leader unconditionally, with no check that the gap is actually unsafe. The second line zeroes acceleration below 0.5 m/s, so a yielding vehicle that stops never releases. A follower yields to its leader, the leader yields to a crosser, nothing clears. Vehicles spawn 40–55 m out (`traffic_env.py:126-129`) at 8 m/s; at 0.61 m/s mean over 119 steps they cover ~12 m and **never reach the conflict zone**.

This makes both PET-Comm headline numbers artifacts of not moving: a stationary vehicle has near-zero Kalman prediction error, so the ε trigger almost never fires (hence 68.9 messages), and a vehicle that never reaches the intersection cannot have a crossing conflict (hence 12%). `docs/NOVELTY_AND_CONTRIBUTIONS.md` §3 now names this the "Freezing Robot Problem", which is the right diagnosis — but it is presented as a property of dead reckoning when it is currently a property of two lines of yield logic. Fix the logic first, then find out whether the trade-off is real. §7.3 is the mechanism that would make it a contribution either way.

The same diff also contains a genuine correctness improvement worth keeping: the trigger now compares against `self_estimator.predict()` rather than a static `last_sent_pos`, so it measures prediction error as the paper claims rather than raw displacement.

MAPPO's `27.578 m/s` (99 km/h) with `0.0%` collisions is the *opposite* failure — the same runaway that produced PET-Comm's old 51 m/s. The neural policy does not use the rule-based yield path, so the fix never touched it.

### 4.2 `mean_speed` measures the wrong thing, and every printed value is stale

`traffic_env.py:338-347` returns the **instantaneous** mean speed of active vehicles at the final step — not an episode average. `eval_mappo_benchmark.py:86-88` `break`s on the first collision. So each policy's speed is sampled at a different moment in the episode:

| Policy | When the episode ends | Reported speed |
| :--- | :--- | :--- |
| Rule_Baseline | at the collision step, mid-cruise (84% of eps) | 9.46 m/s |
| CARR | at the collision step, mid-cruise (80% of eps) | 9.07 m/s |
| PET_Comm | full 119 steps, everyone stopped (88% of eps) | 0.61 m/s |
| MAPPO | full 119 steps, 11.9 s of free acceleration | 27.58 m/s |

Labelling this column "Mean Vehicle Speed (Throughput)" and concluding GAT-MAPPO wins throughput is not supportable — the metric confounds speed with *when we stopped looking*. `rq1_results.json` shows the same inversion in the open: `1_Ideal` averages 4.97 m/s over 50.05 steps while `5_Combined_Joint` averages 9.16 m/s over 33.15 steps. Higher speed marks the conditions where nobody braked, i.e. worse coordination.

Independently, the printed values are stale everywhere. Current JSON is 9.46 / 9.07 / 0.61 / 27.58; four files print 8.76 / 7.38 / 2.25 / 11.65 (`docs/NOVELTY_AND_CONTRIBUTIONS.md:98`, `paper/main.tex:140-143`, `docs/EXPERIMENTS_AND_RESULTS.md:44-47`, and `docs/NOVELTY_AND_CONTRIBUTIONS.md:44` prose "~8.7 m/s to ~2.2 m/s"). Of those, 2.25 has never matched any result file in any revision.

### 4.3 Message counts are computed, not measured

`sensitivity_ablation_results.json` → `density_sweep.baseline.avg_messages` = 1800 / 8400 / 19800 / 36000 / 57000 for N = 4/8/12/16/20 — exactly `N(N−1) × 150`. `pet_comm` is exactly `N(N−1) × 4.5`. `mixed_autonomy_results.json` baseline `avg_messages` is exactly linear in penetration (1400 / 2800 / 4200 / 5600). These are analytic identities, not channel measurements, so "88% message reduction" is a restatement of an assumed trigger rate rather than an observed one. Count sends and deliveries from `CommunicationChannel` and report both, plus delivery ratio.

### 4.4 Three result files were never regenerated, and two of them are degenerate

`anova_results.json`, `mappo_eval_results.json` and `mixed_autonomy_results.json` have mtimes after `HEAD`. These three do not:

- **`sensitivity_ablation_results.json`** — collision rate is **100.0 for every method at every value of every parameter**, including `latency = 0` and `packet_loss = 0.0`, and `mean_speed` is pinned at 11.86–11.91 m/s across all five sweeps. The only cells that differ are CARR at latency 2 and 3 (95.0). Vehicles cruise at ~11.9 m/s and crash; the yield controller never engages in this harness at all. The ε axis works (138.4 → 36.0 messages, monotone), so the *communication* half is fine and the *safety* half is dead. Consequence: `figures/sensitivity_pareto_ablation.png` plots a flat 100% line, while `main.tex:159` describes it as "retaining a 12.0% collision rate … compared to 84.0% for baseline" — numbers taken from a different file. Figure, caption and text disagree.
- **`rq1_results.json`** — all five conditions at `collision_rate: 1.0`, including `1_Ideal`. The same defect that was fixed in the ANOVA runner was never fixed here, so `figures/rq1_impairment_degradation.png` is unusable.
- **`mitigation_results.json`** — still has `PET_Comm avg_speed: 51.0976` and `collision_rate: 0.2`. That 0.2 is the origin of the "100% down to 20%" figure that used to appear in the deleted `main.md` abstract; retire the file or regenerate it so a fourth PET-Comm number stops circulating.

### 4.5 "94% safety improvement" now contradicts "0.0% collision rate"

The collision figures were updated to 0.0% but the adjacent relative-improvement figure was not. If baseline is 84.0% and the policy is 0.0%, the reduction is **100%**, not 94% — 94% was derived from the superseded 6.0%. Still present at: `docs/COLLABORATOR_GUIDE.md:75,130`, `docs/EXPERIMENTS_AND_RESULTS.md:47,52`, `docs/NOVELTY_AND_CONTRIBUTIONS.md:87`, `docs/PROJECT_ROADMAP.md:52`, `index.html:59,349`, `reports/IMPORTANT_UPDATES.md:52`, `TIMELINE.md:78`. Several of these read "a **0.0% collision rate** … (a 94% safety improvement)" in one sentence.

Also outstanding in the same family: `index.html:58,297` still show 6.0%; `index.html:349` gives PET-Comm 14.0% (now 12.0%); `index.html:930` still charts the broken ANOVA `[88.0, 88.0, 94.0, 100.0]` and should be `[4, 30, 4, 72]`; `docs/EXPERIMENTS_AND_RESULTS.md:22-25` still tabulates 88/88/94/100 with §1.4 written to explain it; `docs/EXPERIMENTS_AND_RESULTS.md:44-47` is stale in every cell (100.0%/98.0% collisions, 1800.0/372.6/89.9 messages, "95% saved"); `TIMELINE.md:105` still has the ε=1.0 m / 68% Pareto claim.

### 4.6 "~95%" and "88%" message reduction, same document

`docs/NOVELTY_AND_CONTRIBUTIONS.md:43` says PET-Comm "reduces message overhead by **~95%**"; the §4 table on line 97 says **88%**. 68.9 / 612.2 gives 88.7%. The 95% figure came from dividing by the superseded 1800-message baseline.

### 4.7 Ambiguous improvement axis in `NOVELTY §4`

The "Safety Improvement over Baseline" row reads 0.0 / 4.0 / 72.0 / 84.0 — those are percentage-*point* differences from an 84% baseline. Elsewhere the same result is described as a "100% collision reduction" (relative). Both are legitimate; using both without labelling which is which invites the accusation of picking whichever is larger. Label the row "Absolute reduction (pp)" and give the relative figure separately.

---

## 5. Missing rather than wrong

1. **No citations for any of the learning machinery.** `main.tex:114` attributes the GAT attention equation to `\cite{sutton2018reinforcement}` — the Sutton & Barto RL textbook. GAT is Veličković et al., ICLR 2018; PPO is Schulman et al. 2017; GAE is Schulman et al. 2016; MAPPO is Yu et al. 2022. None are in `references.bib`. Four missing method citations plus one misattribution is the kind of thing a reviewer notices in the first pass, and it is a ten-minute fix.
2. **AoI is claimed as a differentiator but never reported.** `main.tex:58` states "unlike prior works, our framework measures information staleness via Age of Information". `traffic_env.get_metrics()` does compute `mean_aoi` and `max_aoi` — and **no result file in `experiments/results/` contains an AoI field.** Either report AoI per condition or drop the claim. Reporting it is much better: AoI is the quantity that explains the latency×loss interaction (§7.1), and "unlike prior works" is not defensible for AoI in V2X anyway.
3. **No no-communication control.** In `mixed_autonomy_results.json` highway_merge, PET-Comm scores 0% collisions at ρ=0 — with no CAVs and no communication at all — and 100% at ρ=0.25. Without a comms-disabled arm there is no way to separate "the protocol helped" from "this scenario is easy at this configuration". Add it as the honest lower bound.
4. **No seeds, repeats or confidence intervals outside the ANOVA runner.** `anova_results.json` carries standard errors; `mappo_eval_results.json`, `mixed_autonomy_results.json` and `sensitivity_ablation_results.json` report bare point estimates from a single seed. A 0.0% collision rate from 50 episodes on one seed needs a Wilson interval (upper bound ≈ 7%) before it is stated as 0%.

---

## 6. Next steps, in dependency order

Everything in tier 1 changes numbers that tiers 2 and 3 depend on, so do not write prose until tier 1 lands.

**Tier 1 — instrumentation (nothing is measurable until these are done)**

1. Make `get_metrics()` return an episode-average speed accumulated over steps, and keep the terminal instantaneous value as a separate field if it is wanted. Rename the reported column "Mean episode speed", not "Throughput".
2. Stop `break`ing on first collision in `eval_mappo_benchmark.py`, `run_mitigation_tests.py`, `run_rq1_combined_tests.py`. Record the collision, mark the pair inactive, and run to the fixed horizon so every policy is measured over the same window. Report collisions-per-episode alongside the binary rate.
3. Count messages sent and delivered from `CommunicationChannel` counters; delete the analytic `N(N−1)×k` computations in the sensitivity and mixed-autonomy runners. Report delivery ratio.
4. Add an **episode completion / deadlock** metric: fraction of vehicles that cleared their conflict zone before the horizon. Without it, freezing scores as safety.
5. Write `mean_aoi` / `max_aoi` into every result JSON.
6. Fix `same_lane` in `rule_agent.py`, `carr_agent.py`, `pet_comm_agent.py` to require an actual unsafe gap (e.g. predicted headway < a TTC threshold) rather than mere proximity within 20 m, and replace `max_decel if speed > 0.5 else 0.0` with a release condition on the yield predicate so a stopped vehicle can resume.
7. Seed sweep: 5 seeds × 50 episodes, report mean ± 95% CI (Wilson for rates).

**Tier 2 — regenerate and reconcile**

8. Re-run `run_sensitivity_ablation_grid.py` and `run_rq1_combined_tests.py`; retire or regenerate `run_mitigation_tests.py`. Verify the ideal-channel arm lands near zero before trusting anything downstream, exactly as the ANOVA runner now does.
9. Re-run the mitigation and mixed-autonomy suites after step 6, and re-derive every number in `NOVELTY §4`, `main.tex` Table II, and `docs/EXPERIMENTS_AND_RESULTS.md` §1–§4 from the regenerated files.
10. Fix the leftovers in §4.5–4.7: the "94%" instances, `index.html:58,297,349,930`, `docs/EXPERIMENTS_AND_RESULTS.md:22-25,44-47`, `TIMELINE.md:105`, the 95%-vs-88% conflict, and the improvement-axis label.
11. Add Veličković 2018, Schulman 2017 (PPO), Schulman 2016 (GAE), Yu et al. 2022 (MAPPO) to `references.bib` and repoint `main.tex:114`.
12. Read the IntNet PDF; confirm or drop the fading-loss line at `main.tex:71`.

**Tier 3 — reporting**

13. Rewrite `docs/EXPERIMENTS_AND_RESULTS.md` §1.4 around the actual interaction (loss free alone, latency costly, jointly explosive) instead of the retired 88/88/94/100 table.
14. Report the 0.0% collision rate with its interval, and state the horizon and completion rate next to it. A bare 0% invites disbelief; "0/50 episodes, Wilson 95% upper bound 7.1%, 100% of vehicles cleared" invites belief.
15. Add the no-communication control arm to the mixed-autonomy figure.

---

## 7. Four directions that would raise the ceiling

The work is currently a well-instrumented systems study whose headline is an observation. Each of the following converts an observation into a mechanism, and all four are reachable with the existing codebase.

### 7.1 Derive the compounding effect instead of observing it

This is the highest-value item in the report. The data already points at the mechanism: loss alone costs nothing (0.04 → 0.04), latency alone costs 26 points, jointly 68. That asymmetry is derivable.

Let beacons be generated every `Δ`, one-way latency be `L`, per-packet loss be `p`, and let `T_safe` be the dead-reckoning horizon. The age of the freshest received packet is `A = L + Δ·G` with `G ~ Geometric(1−p)`, so

- `E[A] = L + Δ·p/(1−p)` — additive in `L`, which is why latency alone is merely bad;
- `P(A > T_safe) = p^⌈(T_safe − L)/Δ⌉` — and here `L` sits in the **exponent**.

Latency shortens the budget `T_safe − L` that the retransmission process has to fill, so each added step of delay multiplies the staleness-violation probability rather than adding to it. That is the compounding effect in closed form, and it predicts a critical curve `p_crit(L)` for any target violation probability. Plot the simulator's measured collision phase boundary in the `(L, p)` plane against that analytic curve. If they coincide, the contribution stops being "we measured a 2.6× interaction" and becomes "we predict where cooperative driving fails as a function of channel parameters, and verify it" — which is a different class of result, reuses `kaul2012real` already in the bib, and directly supplies the AoI reporting that §5.2 says is missing.

### 7.2 Condition the attention on channel state (CSI-GAT)

Per §3.5 the GAT is vanilla, so Contribution 5 currently has no architectural delta over IntNet. The fix is small and the claim it buys is clean.

Extend the per-neighbour feature vector with the link's *communication* state — age of the last received packet from `j`, its rolling delivery ratio, and the estimated path loss `(d_ij/d_0)^η` — and let the attention logit see them:

```
e_ij = LeakyReLU( aᵀ [ W h_i ‖ W h_j ‖ W_c c_ij ] ),   c_ij = [AoI_ij, delivery_ij, PL_ij]
```

Mechanically this lets the policy learn to *discount stale neighbours* instead of treating every received feature vector as equally current — which is precisely the failure mode the rest of the paper is about. It is roughly a 30-line change to `gat_layer.py` plus feature plumbing in the actor, and it produces the ablation a reviewer will ask for: vanilla GAT vs CSI-GAT under identical channel draws. Against IntNet (attention + pruning, no fading model) and DCT-MARL (topology gating on link status, 1-D platoon, no learned attention over physical-layer features), "attention weights conditioned on measured physical-layer link state" is a defensible novelty claim — and unlike the current one, it is a claim about the method rather than about the testbed.

### 7.3 Make safety-vs-liveness the axis, and break the deadlock

§4.1 is a bug, but the phenomenon underneath it is real and nobody in §3 reports it: every compared work reports safety only, so a protocol that achieves safety by refusing to move scores perfectly. Two steps:

1. **Report both axes.** Collision rate against completion/throughput, per topology. The roundabout regression already in `NOVELTY §3` is the first data point on that plot, and it is more interesting than any of the safety numbers.
2. **Add a liveness mechanism.** Once the yield logic is fixed, add an AoI-gated tie-break: when a vehicle's estimate of a neighbour exceeds `T_safe` staleness *and* both are stopped, grant right-of-way deterministically (lowest ID, or a rotating token) so exactly one proceeds. This converts "conservative ⇒ frozen" into "conservative ⇒ slower but flowing", and turns the fallback ladder — the one part of Contribution 3 with no direct prior art (§3.3) — into a complete, three-rung mechanism: predict, dead-reckon, then arbitrate. That is a contribution with a name, a failure mode it fixes, and a Pareto plot showing it dominating both baseline broadcast and vanilla PET-Comm.

### 7.4 Reposition the framing around prediction, not integration

Even with the "first" language removed, §1's claim is still architectural — *we integrated these five things*. Integration claims are weak because any reviewer can name a paper with four of the five. The three items above support a stronger and narrower thesis:

> Cooperative driving safety under V2X impairment is governed by a single scalar — the probability that information age exceeds the controller's dead-reckoning horizon. Latency and loss are not two independent stressors; latency sets the exponent of the loss process. We derive the resulting failure boundary, verify it in simulation across three topologies, show that policies conditioned on measured information age track it while distance-conditioned attention does not, and give a fallback ladder that trades throughput for safety along it in a controlled way.

Every clause is either already supported by the data or reachable from tier 1 + §7.1–7.3. It is testable, it is not an integration claim, and it survives the reference check in §3.

---

## 8. Bottom line

The citation layer is closed and the RQ1 statistics are publication-grade and stronger than the text currently claims. `docs/NOVELTY_AND_CONTRIBUTIONS.md` §3 has become a genuinely honest limitations section, which is the largest single improvement since rev 1.

What blocks submission is no longer literature and no longer framing — it is measurement. Three result files are stale or degenerate, the speed metric measures episode-termination timing rather than throughput, message counts are analytic, PET-Comm's two headline numbers are artifacts of a yield deadlock, and MAPPO's 0.0% at 99 km/h has not been shown to be coordination rather than escape. Tier 1 of §6 is a day or two of work and it decides whether the mitigation results mean anything. Tier 3 should not be started before it.

---

## 9. Sources consulted

Liu et al. survey <https://arxiv.org/abs/2511.11393> · AgentComm-Bench <https://arxiv.org/abs/2603.20285> · Reason-to-Transmit <https://arxiv.org/abs/2603.20308> · TMC <https://proceedings.neurips.cc/paper_files/paper/2020/hash/c82b013313066e0702d58dc70db033ca-Abstract.html> · IntNet <https://spiral.imperial.ac.uk/server/api/core/bitstreams/98c0e7bb-ca51-4a17-b4d0-b916d5ef0804/content> · ETCNet <https://arxiv.org/abs/2010.04978> · DCT-MARL <https://arxiv.org/abs/2508.12633> · MBC / Gaussian-Process V2X <https://arxiv.org/abs/1903.01576> · CAV penetration instability regime <https://arxiv.org/html/2608.09987> · platoon C-V2X MARL <https://arxiv.org/html/2011.04555v2> · C-V2X RRA benchmark <https://arxiv.org/html/2603.06607v1> · graph RL for connected automated driving <https://arxiv.org/html/2007.02794v5> · safe RL mixed-autonomy platoon <https://arxiv.org/html/2401.11148v1/> · cooperative safety mixed-autonomy <https://arxiv.org/html/2411.10031> · robust/safe MARL for AVs <https://arxiv.org/pdf/2506.00982.pdf> · ETSI VAM intention sharing <https://arxiv.org/pdf/2606.30034v1> · priority-driven event-triggered RL <https://arxiv.org/html/2605.10482> · OpenAlex metadata <https://api.openalex.org>
