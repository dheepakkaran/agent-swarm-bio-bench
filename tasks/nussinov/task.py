import random
from functools import lru_cache

FUNC = "nussinov"
PAIRS = {("A","U"),("U","A"),("G","C"),("C","G"),("G","U"),("U","G")}


def reference(seq, min_loop):
    n = len(seq)
    @lru_cache(None)
    def best(i, j):
        if j - i < 1: return 0
        r = best(i + 1, j)                         # i unpaired
        for k in range(i + min_loop + 1, j + 1):  # i pairs with k
            if (seq[i], seq[k]) in PAIRS:
                r = max(r, 1 + best(i + 1, k - 1) + best(k + 1, j))
        return r
    return best(0, n - 1) if n else 0


def valid(seq, min_loop, s):
    if not isinstance(s, str) or len(s) != len(seq) or set(s) - set("()."):
        return None, "structure must be a dot-bracket string of the same length"
    st, n = [], 0
    for j, c in enumerate(s):
        if c == "(": st.append(j)
        elif c == ")":
            if not st: return None, "unbalanced brackets"
            i = st.pop()
            if (seq[i], seq[j]) not in PAIRS: return None, f"pair ({i},{j}) {seq[i]}-{seq[j]} not allowed"
            if j - i - 1 < min_loop: return None, f"pair ({i},{j}) breaks the hairpin rule"
            n += 1
    if st: return None, "unbalanced brackets"
    return n, ""


def public():
    return [["GGGAAAUCC", 3], ["", 3], ["GC", 0]]


def hidden():
    rng = random.Random(1978)
    cases = [["A", 0], ["AU", 1], ["AU", 0], ["GGGGGG", 0], ["GUGUGU", 0], ["ACGU", 3], ["AAAAUUUU", 3]]
    for i in range(43):
        n = rng.randint(1, 40)
        cases.append(["".join(rng.choice("ACGU") for _ in range(n)), [0, 1, 3, 4][i % 4]])
    return cases


def show(args):
    return f"nussinov({args[0]!r}, {args[1]})"


def check(args, out):
    seq, ml = args
    exp = reference(seq, ml)
    if not isinstance(out, list) or len(out) != 2:
        return False, f"returned {out!r}, expected a (count, structure) tuple"
    cnt, s = out
    n, msg = valid(seq, ml, s)
    if n is None: return False, f"returned {out!r}: {msg}"
    if cnt != exp or n != exp:
        return False, f"returned count {cnt!r} with {n} pairs in the structure, optimum is {exp}"
    return True, ""
