# Task: local sequence alignment score with affine gaps

Source: Smith & Waterman, "Identification of common molecular subsequences", J. Mol. Biol. 147:195 (1981);
affine gap recurrences: Gotoh, "An improved algorithm for matching biological sequences", J. Mol. Biol. 162:705 (1982).

Write `local_align_score(a: str, b: str, match: int, mismatch: int, gap_open: int, gap_extend: int) -> int`.

Mathematical description. A local alignment pairs a substring of `a` with a substring of `b`, keeping order, where
each column is either two aligned characters or a character against a gap. Its score is the sum of:
- `+match` for each column with equal characters, `-mismatch` for each column with different characters;
- for each maximal run of k ≥ 1 consecutive gap columns in the same sequence: `-(gap_open + (k-1) * gap_extend)`.
  A gap run in `a` may directly follow a gap run in `b` (they are two separate runs).
Return the maximum score over all local alignments; the empty alignment scores 0, so the answer is ≥ 0.
All parameters are non-negative integers (`match` ≥ 1). Sequences may be empty, any characters (DNA or protein letters).

Public examples:
- `local_align_score("ACACACTA", "AGCACACA", 2, 1, 2, 1)` → `10`
- `local_align_score("", "ACGT", 2, 1, 2, 1)` → `0`
- `local_align_score("AAAAGGGGTTTT", "AAAATTTT", 1, 1, 3, 1)` → `4`
