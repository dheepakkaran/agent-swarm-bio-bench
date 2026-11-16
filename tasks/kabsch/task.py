import math, random
import numpy as np
from Bio.SVDSuperimposer import SVDSuperimposer

FUNC = "kabsch_rmsd"


def reference(P, Q):
    P, Q = np.array(P, float), np.array(Q, float)
    if len(P) == 1:
        return 0.0
    s = SVDSuperimposer(); s.set(Q, P); s.run()
    return float(s.get_rms())


def _rot(rng):
    q = np.array([rng.gauss(0, 1) for _ in range(4)]); q /= np.linalg.norm(q)
    w, x, y, z = q
    return np.array([[1 - 2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                     [2*(x*y+w*z), 1 - 2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1 - 2*(x*x+y*y)]])


def public():
    return [[[[0,0,0],[1,0,0],[0,1,0]], [[0,0,0],[1,0,0],[0,1,0]]],
            [[[1,0,0],[0,1,0],[0,0,1]], [[0,1,0],[-1,0,0],[0,0,1]]],
            [[[0,0,0],[2,0,0]], [[0,0,0],[1,0,0]]]]


def hidden():
    rng = random.Random(1976)
    cases = [[[[1.5, -2, 3]], [[10, 10, 10]]]]
    for i in range(39):
        n = rng.choice([2, 3, 4, 8, 20, 50])
        P = np.array([[rng.uniform(-20, 20) for _ in range(3)] for _ in range(n)])
        kind = i % 5
        if kind == 1: P[:, 2] = 0.0                                            # coplanar
        if kind == 2: d = np.array([1.0, 2.0, -1.0]); P = np.outer([rng.uniform(-5, 5) for _ in range(n)], d)  # collinear
        Q = P @ _rot(rng).T + np.array([rng.uniform(-50, 50) for _ in range(3)])
        if kind == 3: Q = Q * np.array([-1, 1, 1])                             # mirror image: no proper rotation fits
        if kind in (0, 3, 4): Q = Q + np.array([[rng.gauss(0, 0.8) for _ in range(3)] for _ in range(n)])
        if kind == 4: P = P * 1000.0; Q = Q * 1000.0                           # large coordinates
        cases.append([P.round(6).tolist(), Q.round(6).tolist()])
    return cases


def show(args):
    P, Q = args
    s = f"kabsch_rmsd(P, Q) with N={len(P)}"
    return s + (f", P={P}, Q={Q}" if len(P) <= 3 else "")


def check(args, out):
    exp = reference(*args)
    try:
        v = float(out)
        if math.isfinite(v) and abs(v - exp) <= 1e-6 * max(1.0, abs(exp)):
            return True, ""
    except Exception:
        pass
    return False, f"returned {out!r}, expected {exp:.6f}"
