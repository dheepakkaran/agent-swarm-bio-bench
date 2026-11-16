"""The references must be right before any agent is scored against them."""
import itertools, random
import numpy as np
from tasks.alignment import task as al
from tasks.kabsch import task as kb
from tasks.nussinov import task as nu


def gotoh(a, b, ma, mi, go, ge):
    """Independent O(nm) affine-gap local alignment (3 matrices)."""
    NEG = -10**9
    n, m = len(a), len(b)
    H = [[0]*(m+1) for _ in range(n+1)]; E = [[NEG]*(m+1) for _ in range(n+1)]; F = [[NEG]*(m+1) for _ in range(n+1)]
    best = 0
    for i in range(1, n+1):
        for j in range(1, m+1):
            E[i][j] = max(H[i][j-1] - go, E[i][j-1] - ge, F[i][j-1] - go)
            F[i][j] = max(H[i-1][j] - go, F[i-1][j] - ge, E[i-1][j] - go)
            H[i][j] = max(0, H[i-1][j-1] + (ma if a[i-1] == b[j-1] else -mi), E[i][j], F[i][j])
            best = max(best, H[i][j])
    return best


def test_alignment_reference_matches_gotoh():
    for args in al.hidden() + al.public():
        assert al.reference(*args) == gotoh(*args), args


def test_alignment_public_values():
    assert [al.reference(*a) for a in al.public()] == [10, 0, 4]


def kabsch_np(P, Q):
    P, Q = np.array(P, float), np.array(Q, float)
    P = P - P.mean(0); Q = Q - Q.mean(0)
    U, S, Vt = np.linalg.svd(P.T @ Q)
    d = np.sign(np.linalg.det(Vt.T @ U.T)) or 1.0
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return float(np.sqrt(((P @ R.T - Q) ** 2).sum(1).mean()))


def test_kabsch_reference_matches_numpy_and_rejects_mirrors():
    for args in kb.hidden() + kb.public():
        assert abs(kb.reference(*args) - kabsch_np(*args)) < 1e-6 * max(1, kb.reference(*args)), len(args[0])
    mirrored = [c for i, c in enumerate(kb.hidden()[1:]) if i % 5 == 3 and len(c[0]) >= 4]  # 2-3 points are planar: a mirror fits
    assert all(kb.reference(*c) > 1.0 for c in mirrored)   # a mirror image cannot be fitted by a rotation
    assert [round(kb.reference(*a), 9) for a in kb.public()] == [0.0, 0.0, 0.5]


def exhaustive(seq, ml):
    """Backtracking over sets of allowed pairs (no DP): every compatible pair set is visited."""
    n = len(seq)
    cand = [(i, j) for i in range(n) for j in range(i + ml + 1, n) if (seq[i], seq[j]) in nu.PAIRS]
    best = 0
    def compatible(p, chosen):
        i, j = p
        for k, l in chosen:
            if len({i, j, k, l}) < 4 or i < k < j < l or k < i < l < j: return False
        return True
    def go(idx, chosen):
        nonlocal best
        best = max(best, len(chosen))
        if len(chosen) + (len(cand) - idx) <= best: return
        for t in range(idx, len(cand)):
            if compatible(cand[t], chosen):
                chosen.append(cand[t]); go(t + 1, chosen); chosen.pop()
    go(0, [])
    return best


def test_nussinov_reference_matches_exhaustive():
    rng = random.Random(7)
    for _ in range(150):
        s = "".join(rng.choice("ACGU") for _ in range(rng.randint(0, 10)))
        ml = rng.choice([0, 1, 3])
        assert nu.reference(s, ml) == exhaustive(s, ml), (s, ml)
    assert nu.check(["GGGAAAUCC", 3], [3, "(((...)))"])[0]
    assert not nu.check(["GGGAAAUCC", 3], [3, "((((..))))"[:9]])[0]
