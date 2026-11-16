# Task: minimal RMSD after optimal rigid superposition (Kabsch)

Source: Kabsch, "A solution for the best rotation to relate two sets of vectors", Acta Cryst. A32:922 (1976);
correction for improper rotations: Kabsch, Acta Cryst. A34:827 (1978).

Write `kabsch_rmsd(P, Q) -> float`. `P` and `Q` are lists of N ≥ 1 points `[x, y, z]` (same N, point i of P
corresponds to point i of Q), e.g. protein C-alpha coordinates.

Mathematical description. Find the rotation R (a proper rotation: Rᵀ R = I and det R = +1, so no mirror images)
and translation t that minimize E = (1/N) Σᵢ ‖R pᵢ + t − qᵢ‖². Return RMSD = √E at the optimum.
Kabsch's solution: center both sets on their centroids, form the 3×3 covariance H = Σ pᵢ' qᵢ'ᵀ, take its SVD,
and build R from the singular vectors, flipping the sign of the smallest singular direction when needed so that
det R = +1. Must also work for degenerate inputs (N = 1, 2, collinear or coplanar points). Return a Python float.
Answers are checked to 1e-6 absolute tolerance.

Public examples:
- `kabsch_rmsd([[0,0,0],[1,0,0],[0,1,0]], [[0,0,0],[1,0,0],[0,1,0]])` → `0.0`
- `kabsch_rmsd([[1,0,0],[0,1,0],[0,0,1]], [[0,1,0],[-1,0,0],[0,0,1]])` → `0.0` (rotation about z)
- `kabsch_rmsd([[0,0,0],[2,0,0]], [[0,0,0],[1,0,0]])` → `0.5`
