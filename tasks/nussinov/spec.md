# Task: RNA secondary structure by base-pair maximization (Nussinov)

Source: Nussinov, Pieczenik, Griggs & Kleitman, "Algorithms for loop matchings", SIAM J. Appl. Math. 35:68 (1978).

Write `nussinov(seq: str, min_loop: int) -> tuple[int, str]`.

Mathematical description. `seq` is an RNA string over A, C, G, U (may be empty). A secondary structure is a set of
pairs (i, j), i < j, such that:
- each position is in at most one pair;
- each pair is allowed: A–U, U–A, G–C, C–G, G–U, U–G;
- hairpin rule: j − i − 1 ≥ `min_loop` (at least `min_loop` unpaired-or-other positions strictly between i and j);
- no pseudoknots: no two pairs (i, j), (k, l) with i < k < j < l.
Return `(count, structure)` where `count` is the maximum possible number of pairs and `structure` is one optimal
structure in dot-bracket form: a string of length len(seq) with "(" at i and ")" at j for each pair, "." elsewhere.
`min_loop` is an integer ≥ 0. Any optimal structure is accepted.

Public examples:
- `nussinov("GGGAAAUCC", 3)` → `(3, "(((...)))")`
- `nussinov("", 3)` → `(0, "")`
- `nussinov("GC", 0)` → `(1, "()")`
