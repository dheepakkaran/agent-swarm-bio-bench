# agent-swarm-bio-bench

Does a small **agent swarm** write more correct scientific code than **one agent**, at the same cap of model calls?
And does the swarm's **critic** matter? A pre-registered, small, controlled experiment on three classic
computational biology methods, each specified from its original paper's math and scored on hidden tests
against established implementations (Biopython).

**Project page + 90 s overview film:** https://dheepakkaran.github.io/agent-swarm-bio-bench/#overview

[![Overview film (silent preview, 4x speed)](docs/media/keynote.webp)](https://dheepakkaran.github.io/agent-swarm-bio-bench/#overview)

## Result (27 runs, Claude Haiku 5.5, `RESULTS.md`)

| Arm | Runs fully correct on hidden tests | Mean model calls | Mean tokens | Median wall time |
|---|---|---|---|---|
| single agent (refines on its own self-test) | 9/9 | 1.56 | 12,634 | 99 s |
| swarm: planner → 3 parallel implementers → critic → refine | 9/9 | 5.22 | 75,752 | 279 s |
| swarm without critic (ablation) | 9/9 | 4.00 | 39,793 | 128 s |

- **Tie at the ceiling.** Every arm ended with a fully correct answer in every run, so H1 (swarm beats single)
  and H2 (the critic helps) are **not supported** at this difficulty. The swarm cost **6.0×** the tokens and 2.8× the time.
- **Where code went wrong, all arms recovered.** Only alignment (affine gaps) produced wrong code: 2 of 9 single-agent
  first drafts passed 46/60 hidden tests and were fixed after their own self-test failed; 3 swarm implementer drafts
  timed out (too slow), and selection simply picked a correct sibling.
- **The critic raised only false alarms:** both refine calls it triggered were spent on answers that were already correct.
  Single agents' self-tests also failed on correct code in 3 of 5 refines (wrong expected values in their own tests).

Plain reading: on well-known algorithms a single agent with a test loop is enough; coordination only adds cost here.
The interesting test is harder or less familiar methods, where first drafts fail more often (next step).

## How it works

```
tasks/<name>/spec.md      math from the paper + 3 public examples (all agents see this)
tasks/<name>/task.py      hidden tests + Biopython / own reference (no agent sees this)
swarm/run.py              arms, call cap 6, harness runs all code (agents have no tools)
swarm/agents.py           headless `claude -p` agent turns, 6 in parallel, 1 retry on a failed call
swarm/ledger.py           SQLite shared state: every run and every call (tokens, time, errors)
scripts/report.py         ledger → results/summary.json + RESULTS.md
docs/00-scope.md          question, arms, metrics and hypotheses, committed before any run
```

| Task | Paper | Reference used for hidden tests |
|---|---|---|
| Local alignment, affine gaps | Smith & Waterman 1981, Gotoh 1982 | Biopython `PairwiseAligner`, cross-checked by an own Gotoh DP |
| Optimal superposition RMSD | Kabsch 1976/1978 | Biopython `SVDSuperimposer`, cross-checked by NumPy SVD (mirror cases included) |
| RNA base-pair maximization | Nussinov et al. 1978 | own DP, cross-checked by brute-force backtracking; any optimal dot-bracket accepted |

## Run it

```bash
uv sync
uv run pytest -q                        # 8 tests: references + harness + ledger
uv run python -m swarm.run --reps 3     # needs Claude Code logged in; resumes from the ledger
uv run python scripts/report.py
```

## Limits

n = 3 reps × 3 tasks per arm, one model, textbook algorithms the model has likely seen; the call cap is equal but
token use is not (reported instead); "first draft" for the swarm = implementer 1. Agent traces stay local
(`results/runs/`, gitignored). See `FAILURES.md`.
