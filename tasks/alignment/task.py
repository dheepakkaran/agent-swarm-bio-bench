import random
from Bio import Align

FUNC = "local_align_score"
PARAMS = [(2, 1, 2, 1), (1, 1, 3, 1), (5, 4, 10, 1), (1, 3, 2, 2), (3, 2, 4, 0), (2, 3, 1, 1), (1, 0, 5, 5), (4, 1, 6, 3)]


def reference(a, b, match, mismatch, gap_open, gap_extend):
    if not a or not b:
        return 0
    al = Align.PairwiseAligner()
    al.mode = "local"
    al.match_score, al.mismatch_score = match, -mismatch
    al.open_gap_score, al.extend_gap_score = -gap_open, -gap_extend
    return max(0, int(round(al.score(a, b))))


def public():
    return [["ACACACTA", "AGCACACA", 2, 1, 2, 1], ["", "ACGT", 2, 1, 2, 1], ["AAAAGGGGTTTT", "AAAATTTT", 1, 1, 3, 1]]


def hidden():
    rng = random.Random(20261116)
    cases = [["A", "A", 1, 1, 1, 1], ["A", "C", 1, 1, 1, 1], ["", "", 2, 1, 2, 1], ["ACGT", "", 2, 1, 2, 1]]
    for i in range(56):
        alpha = "ACGT" if i % 2 == 0 else "ACDEFGHIKLMNPQRSTVWY"
        n, m = rng.randint(1, 40), rng.randint(1, 40)
        a = "".join(rng.choice(alpha) for _ in range(n))
        if i % 3 == 0:  # b = mutated copy with indels: long gaps matter
            b = list(a)
            for _ in range(rng.randint(1, 4)):
                p = rng.randrange(len(b) + 1)
                if rng.random() < 0.5: b[p:p] = list("".join(rng.choice(alpha) for _ in range(rng.randint(1, 6))))
                else: del b[p:p + rng.randint(1, 6)]
            b = "".join(b) or alpha[0]
        else:
            b = "".join(rng.choice(alpha) for _ in range(m))
        cases.append([a, b, *PARAMS[i % len(PARAMS)]])
    return cases


def show(args):
    a, b, *p = args
    return f"local_align_score({a!r}, {b!r}, {', '.join(map(str, p))})"


def check(args, out):
    exp = reference(*args)
    try:
        if int(out) == exp and float(out) == float(int(out)):
            return True, ""
    except Exception:
        pass
    return False, f"returned {out!r}, expected {exp}"
