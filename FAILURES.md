# Failures and surprises (logged as they happened)

1. **Ceiling.** All 27 runs passed all hidden tests, so the arms cannot be separated. Tasks are too familiar for the model; the pre-registered hypotheses are not supported rather than refuted.
2. **Critic false alarms.** In 2 of 9 swarm runs the critic's own checker flagged correct code and spent a refine call; the refine kept the code correct. A critic adds cost when its checks are wrong.
3. **Wrong self-tests.** Single agents' self-tests failed on already correct code in 3 of 5 refines (e.g. a wrong expected RMSD for a rotated triangle in `kabsch-single-r1`).
4. **Real bugs only on affine gaps.** 2 single-agent first drafts scored 46/60 on alignment (e.g. 13 instead of 14), both fixed after one refine.
5. **Slow drafts.** 3 swarm implementer drafts for alignment timed out at 60 s on the hidden tests (0/60); selection by public examples + critic picked a correct sibling. Speed was never asked for in the spec.
6. **Laptop sleep.** 3 runs show ~2 h wall time (one critic call hit the 300 s timeout after resume and was retried). Medians are reported for that reason.
7. **My own test bugs.** First brute-force Nussinov checker (all subsets) was too slow; replaced by backtracking. A mirror-image Kabsch check wrongly assumed 2–3 points cannot be fitted by a rotation (they are planar, so they can).
