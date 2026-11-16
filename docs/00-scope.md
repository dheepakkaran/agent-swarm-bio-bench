# Scope and pre-registered question (written 2026-11-16, committed before any agent run)

## Question
At the same cap of model calls, does a small agent swarm (planner → 3 parallel implementers → critic
with its own tests → 1 refine) write more correct scientific code than one agent refining its own work?
Does the critic matter (ablation: same swarm, critic replaced by each implementer's self-tests)?

## Tasks (classic computational biology methods, spec written from the original paper's math)
1. Local sequence alignment with affine gaps: Smith & Waterman (1981), affine gaps per Gotoh (1982).
   Reference: Biopython `PairwiseAligner` (local mode).
2. Optimal rigid superposition RMSD of two 3-D point sets: Kabsch (1976), rotations only.
   Reference: Biopython `SVDSuperimposer`.
3. RNA secondary structure by base-pair maximization: Nussinov et al. (1978), returns count + dot-bracket.
   Reference: own DP, cross-checked against exhaustive enumeration in `tests/`.

## Arms (each capped at 6 model calls per run, same model: Claude Haiku 5.5 via headless `claude -p`, no tools)
- `single`: 1 agent writes solution + self-test, then refines on public-example and self-test failures (≤ 5 refines).
- `swarm`: planner (pitfalls + 3 different approaches) → 3 implementers in parallel → critic writes an independent
  checker (brute force / properties) → harness runs it on all 3 → best candidate refined once with the failing cases.
- `swarm_nocritic` (ablation): same planner + 3 implementers, each with a self-test; best by public + self-test;
  ≤ 2 refines on its own failures.
The harness executes all code (agents have no tools). Hidden tests are never shown to any agent; they score the final answer only.

## Metrics
- Solution quality: share of hidden tests passed. Reliability: share of runs passing all hidden tests.
- Time to solution: wall seconds per run. Compute: model calls and tokens per run (reported, cap is equal).

## Hypotheses (fixed before running)
- H1: `swarm` passes all hidden tests in more runs than `single`.
- H2: `swarm` beats `swarm_nocritic` (the critic is what helps).
- Small n (3 tasks × 3 reps per arm): results are descriptive, no significance claims.
