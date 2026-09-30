# Search algorithms for the offline build optimiser

**Question.** Which search/optimisation algorithm best fits an offline build optimiser for this
generator: ~20 stochastic decision points, hard legality constraints (prerequisites, typed-bonus
non-stacking), a noisy Monte Carlo fitness (rolled ability scores averaged per candidate), a
per-axis fitness profile (ratios vs a CR benchmark table, later a combat sim), seven roles
optimised separately at level 10, baseline = hand-written policy "V4".

**Method.** Web survey, primary sources preferred (arXiv / proceedings pages linked below). I found
**no published D&D/Pathfinder build optimiser** in the academic literature (searches for
GA / annealing on D&D / Pathfinder character builds returned only unrelated papers and forum
threads). Closest prior art is collectible-card deck search (Hearthstone), which has the same
shape: a combinatorial legal-set space, a noisy game-simulation fitness, and a wish for several
distinct good answers. Where a claim below is my own inference rather than a cited result, it is
marked **[inference]**. Evals/s figures are order-of-magnitude assumptions, not measurements.

## 0. The problem, stated as an optimisation problem

- **Genotype.** Not a flat vector. The generator is a decision *sequence* where later options
  depend on earlier ones (class -> archetype -> feats legal given prerequisites). The natural
  genotype is the **policy parameters / decision list**, re-decoded by the generator's own
  legality logic, not raw picks. **[inference]** This is the most important design choice: if the
  genotype is "a list of decisions the generator replays and repairs", every algorithm below gets
  constraint handling for free, because illegal children cannot be constructed.
- **Noise.** Each evaluation = N rolled stat arrays averaged. Variance is high relative to the
  gap between good builds, so comparing two builds from one evaluation each is unsafe.
- **Objectives.** A vector (to-hit, DPR, AC, HP, saves, DC ...). Roles are *different weightings /
  feasibility regions* of that vector: either seven scalarisations, or one Pareto/QD run projected
  per role.
- **Beat V4.** Anything that keeps V4 as a seed/incumbent and only accepts a change when a paired
  comparison wins is safe by construction.

## 1. Candidates

### 1.1 Generate-N-and-pick (random-restart baseline)
- Eval assumptions: any cost; noise handled by averaging; no model of structure.
- Constraints: free (generator only emits legal builds). Multi-objective: scalarise the profile per
  role; Pareto-filtering the pool is trivial.
- Strength: zero implementation risk, unbiased, embarrassingly parallel, an honest yardstick for
  every other method. Weakness: sample-inefficient when ~20 choices interact; the top 0.01% of
  builds are exponentially rare.
- Verdict: **always implement first**, keep as the control for every other method.

### 1.2 Genetic / evolutionary algorithms
- Precedent: García-Sánchez et al., *Evolutionary Deckbuilding in Hearthstone* (IEEE CIG 2016) used
  a GA with fitness delegated to a simulator that plays each deck against a panel of human-made
  decks [1]. Works for legal-set spaces with a noisy simulator fitness.
- Assumptions: population-based, roughly 10^3-10^5 evaluations total (population x generations);
  tolerates noise because selection averages over the population (runtime-analysis work on
  NSGA-II under noise [5]).
- Constraints: the classic difficulty is crossover producing illegal children. Fix: crossover at
  the *decision-list* level and **repair by replaying through the generator** (prefix from parent
  A, later choices from parent B kept only where still legal), or mutate only. **[inference]**
- Multi-objective: see 1.3 / 1.4.
- Verdict: best general-purpose engine once evals/s is moderate.

### 1.3 NSGA-II (multi-objective GA)
- Deb et al., IEEE TEC 2002: fast non-dominated sort + crowding distance, elitist [2].
- Fit: natural for a *profile* fitness; returns a Pareto front that can be sliced per role.
- Noise weakness, documented: elitism plus noise lets an overestimated point sit on the front
  indefinitely; the literature fixes this with resampling, fixed-budget or sequential/adaptive
  [5][6]. NSGA-II therefore needs per-individual replication or re-evaluation of front members.
- Weakness for us: crowding distance spreads along the *front*, not across *build style*
  (class/archetype). With 6+ objectives non-dominated sorting degrades (most of the population
  becomes non-dominated) **[inference, standard many-objective caveat]**. Prefer scalarising per
  role (1.2) or QD (1.4).

### 1.4 MAP-Elites / quality-diversity
- Mouret & Clune 2015: keep the best solution in each cell of a user-chosen behaviour grid; yields
  a map of high performers and how traits trade off [3].
- Hearthstone precedent, the closest analogue to this task: Fontaine et al., GECCO 2019,
  MAP-Elites with sliding boundaries for deck spaces [7]; Zhang et al., GECCO 2022, Deep Surrogate
  Assisted MAP-Elites, which states plain MAP-Elites needs a *large number of expensive
  evaluations* and cuts them with an online-trained surrogate of game outcomes [8].
- Noise: plain MAP-Elites overwrites a cell on one lucky evaluation; adaptive-sampling variants for
  noisy domains exist [9].
- Fit: behaviour axes = (class/archetype family, melee/ranged/caster, martial vs spell share,
  Spheres/PoW/vanilla). The 7 roles can be a *niche axis*, so one QD run yields a role x style
  atlas instead of 7 runs. Good for a generator whose job is variety. Constraints via the repair
  scheme in 1.2. Multi-objective: one scalar per cell (role score), or CMA-ME [10].
- Cost: largest evaluation budget of all (10^4-10^6); needs a settled noise policy.

### 1.5 MCTS over the decision tree
- Reference: Browne et al. survey, IEEE TCIAIG 2012 [11]. Built for sequential decisions with a
  *terminal reward from a rollout*, which matches "pick class, then race, ... then evaluate".
- Good: constraints native (only legal children exist); noise native (UCT averages rollouts);
  anytime.
- Bad here **[inference]**: (a) reward only at depth ~20 and the tree is wide (hundreds of feats),
  so statistics spread thin; (b) strongly *interacting* choices (feat A only good with class B)
  share poorly across siblings; (c) scalar reward; multi-objective MCTS is research-grade. Rolling
  horizon evolution matches or beats MCTS in multi-action game settings [12]. MCTS plans one game;
  it is not obviously the tool for tuning a static artefact with a long decision list.
- Niche use: a *completion* operator (fix the first k decisions, MCTS the rest).

### 1.6 Bayesian optimisation and CMA-ES
- **BO.** GP models are sample-efficient on expensive noisy functions (seconds-hours per eval).
  Combinatorial/categorical variants exist (BOCS [13], COMBO [14]) but assume scarce evaluations
  and a tractable kernel; legality constraints and a ~20-variable conditional space are awkward,
  and a vector fitness needs multi-objective acquisition. Right tool only if each eval is
  seconds-to-minutes (high-fidelity combat sim).
- **CMA-ES.** Strong for continuous black-box optimisation with noise tolerance via large
  populations [4]; mixed-integer variants exist [15][16]. Our genotype is mostly categorical and
  conditional; CMA-ES fits **only the continuous slice**: V4's numeric knobs (stat-placement
  weights, feat-category weights, bucket priorities). **[inference]**
- Both lose as primary engine: categorical/conditional structure, constraints and vector fitness
  are off their sweet spot.

### 1.7 Reinforcement learning
- Assumes very many cheap evaluations (10^6+), a learned policy and a scalar reward; training
  instability, reward shaping and per-role conditioning add cost. The task is one-shot
  construction with no environment dynamics, so RL's strength (credit assignment through time) is
  mostly unused **[inference]**. It amounts to learning a better V4, which GA/QD do with less
  machinery. Loses on engineering cost and debuggability. Reconsider only with >10^6 evals of
  cheap compute and a need for a *stochastic generator policy* as the product.

## 2. Cross-cutting techniques that matter more than the algorithm

1. **Common random numbers / paired evaluation.** Score two builds on the *same* rolled arrays;
   variance of the difference collapses. Cheapest noise fix available. **[inference]**
2. **Racing / successive halving.** Score all candidates cheaply, re-score only survivors (same
   idea as sequential resampling in noisy NSGA-II [5][6]).
3. **Replicate the incumbent.** V4 and every elite get re-scored each generation so an
   overestimated elite is caught (the documented elitism-under-noise failure [6]).
4. **Two-tier fitness.** Static CR-ratio profile as the inner loop; combat sim only to re-rank the
   final few hundred (surrogate-style funnel, cf. [8]).
5. **Hold-out check.** Finalists must beat V4 on a fresh seed set, not the search set (selection
   bias).

## 3. Ranking as a function of evaluations / second

"Eval" = one candidate scored (N rolled stat arrays averaged). Assume an overnight run, ~10^5 s.

### < 10 evals/s (total < ~10^6; typical of a combat sim)
1. **Generate-N-and-pick with racing + paired seeds**, V4 and its one-gene mutants in the pool;
   then (1+lambda) hill-climb on the top few (the GA degenerate case).
2. **Small GA (pop 20-50), replicated elites, scalarised per role.**
3. BO only if below ~1 eval/s *and* the free parameters are V4's continuous knobs.
- Lose: MAP-Elites (archive fills too slowly; [8] needed surrogates), NSGA-II (resampling
  multiplies cost), MCTS (too many rollouts), RL (hopeless).

### 10-1000 evals/s (10^6-10^8 total; expected regime for the static CR-ratio profile)
1. **GA with decision-list crossover + repair, scalarised per role**, V4 injected into the initial
   population; tune V4's numeric knobs in parallel with CMA-ES.
2. **MAP-Elites over role x build-style niches**, seeded from the GA elites: best fit to the
   generator's real goal (variety of legal strong builds); add adaptive sampling [9].
3. Generate-N-and-pick as control; MCTS as a completion operator if a prefix is fixed.
- Lose: NSGA-II (6+ objective front is nearly all non-dominated; cannot slice per role cleanly;
  noise needs resampling [5][6]), BO/COMBO (kernel + legality mismatch), RL.

### > 1000 evals/s (vectorised or cached; > 10^8 total)
1. **MAP-Elites / CMA-ME quality-diversity as the main engine** [3][10], producing the role x
   style atlas directly; spend surplus throughput on replication to tame noise.
2. **NSGA-II or a many-objective variant** only if the deliverable is a true Pareto front rather
   than seven role-weighted answers [2].
3. **RL** becomes defensible only here, and only if the goal is a replacement stochastic policy.
- Lose: BO (modelling costs more than evaluating), plain generate-N-and-pick (valid as control but
  dominated on efficiency).

## 4. Recommendation in one line
Start with the baseline (paired seeds, V4 in the pool), graduate to a **repair-based GA per role**
once throughput exceeds ~10/s, add **MAP-Elites over role x style** above ~100/s, and use CMA-ES
solely for V4's numeric weights. Do not start with MCTS, BO or RL.

## 5. Open questions (not answerable from the literature)
- Measured evals/s of `generate_random_char()` plus scoring: unknown; it decides the tier.
- How much of V4's hand tuning is numeric (CMA-ES-able) vs categorical rules?
- Variance: how many stat arrays per candidate make a 0.05 ratio gap visible? Measure before
  choosing a population size.
- Are the seven roles truly separate fitness functions or views of one shared profile? That decides
  "7 GA runs" vs "one QD run".

## Sources
1. García-Sánchez et al., Evolutionary Deckbuilding in Hearthstone, IEEE CIG 2016 - https://www.semanticscholar.org/paper/Evolutionary-deckbuilding-in-hearthstone-Garc%C3%ADa-S%C3%A1nchez-Tonda/1e9aa5dd47c165d8dfe155f375c0aa6023a3b3c6
2. Deb et al., A fast and elitist multiobjective genetic algorithm: NSGA-II, IEEE TEC 6(2), 2002 - https://sci2s.ugr.es/sites/default/files/files/Teaching/OtherPostGraduateCourses/Metaheuristicas/Deb_NSGAII.pdf
3. Mouret & Clune, Illuminating search spaces by mapping elites, 2015 - https://arxiv.org/abs/1504.04909
4. Hansen, The CMA Evolution Strategy: A Tutorial, 2016 - https://arxiv.org/abs/1604.00772
5. Analysing the Robustness of NSGA-II under Noise - https://arxiv.org/pdf/2306.04525
6. Adaptive Resampling with Bootstrap for Noisy Multi-Objective Optimization Problems - https://arxiv.org/pdf/2503.21495
7. Fontaine et al., Mapping Hearthstone Deck Spaces through MAP-Elites with Sliding Boundaries, GECCO 2019 - https://arxiv.org/pdf/1904.10656
8. Zhang et al., Deep Surrogate Assisted MAP-Elites for Automated Hearthstone Deckbuilding, GECCO 2022 - https://arxiv.org/pdf/2112.03534
9. MAP-Elites for noisy domains by adaptive sampling, GECCO 2019 - https://dl.acm.org/doi/10.1145/3319619.3321904
10. Fontaine et al., Covariance Matrix Adaptation for the Rapid Illumination of Behavior Space (CMA-ME) - https://arxiv.org/pdf/1912.02400
11. Browne et al., A Survey of Monte Carlo Tree Search Methods, IEEE TCIAIG 2012 - https://repository.essex.ac.uk/4117/
12. Rolling Horizon Evolutionary Algorithms for General Video Game Playing - https://arxiv.org/pdf/2003.12331
13. Baptista & Poloczek, Bayesian Optimization of Combinatorial Structures (BOCS) - https://arxiv.org/pdf/1806.08838
14. Oh et al., Combinatorial Bayesian Optimization using the Graph Cartesian Product (COMBO), NeurIPS 2019 - https://arxiv.org/abs/1902.00448
15. (1+1)-CMA-ES with Margin for Discrete and Mixed-Integer Problems - https://arxiv.org/pdf/2305.00849
16. LB+IC-CMA-ES: Two Simple Modifications of CMA-ES to Handle Mixed-Integer Problems - https://link.springer.com/chapter/10.1007/978-3-031-70068-2_18
