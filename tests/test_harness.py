"""Harness pieces that decide scores: candidate execution, block parsing, ledger."""
from pathlib import Path
from swarm import agents, ledger
from tasks import common
from tasks.nussinov import task as nu


def test_evaluate_scores_a_correct_and_a_broken_candidate(tmp_path):
    good = tmp_path / "good.py"; good.write_text(   # reference DP + traceback = a known-correct candidate
        "import sys\nsys.setrecursionlimit(10000)\n" + Path(nu.__file__).read_text() +
        "\ndef nussinov(seq, min_loop):\n    n = len(seq); best = {}\n"
        "    def tb(i, j):\n        if j - i < 1: return ''.join('.' for _ in range(max(0, j - i + 1)))\n"
        "        v = reference(seq[i:j+1], min_loop)\n"
        "        if reference(seq[i+1:j+1], min_loop) == v: return '.' + tb(i + 1, j)\n"
        "        for k in range(i + min_loop + 1, j + 1):\n"
        "            if (seq[i], seq[k]) in PAIRS and 1 + reference(seq[i+1:k], min_loop) + reference(seq[k+1:j+1], min_loop) == v:\n"
        "                return '(' + tb(i + 1, k - 1) + ')' + tb(k + 1, j)\n"
        "    s = tb(0, n - 1) if n else ''\n    return reference(seq, min_loop), s\n")
    bad = tmp_path / "bad.py"; bad.write_text("def nussinov(seq, min_loop):\n    return 0, '.' * len(seq)\n")
    p, t, f = common.evaluate("nussinov", good, nu.hidden())
    assert p == t, f[:3]
    p2, t2, f2 = common.evaluate("nussinov", bad, nu.hidden())
    assert p2 < t2 and f2


def test_crashing_and_hanging_candidates_score_zero(tmp_path):
    c = tmp_path / "c.py"; c.write_text("raise SystemExit('boom')\n")
    assert common.evaluate("kabsch", c, [[[[0, 0, 0]], [[1, 1, 1]]]])[0] == 0
    h = tmp_path / "h.py"; h.write_text("def kabsch_rmsd(P, Q):\n    while True: pass\n")
    assert common.evaluate("kabsch", h, [[[[0, 0, 0]], [[1, 1, 1]]]], timeout=2)[0] == 0


def test_block_parsing():
    t = "x\n```python solution\ndef f(): pass\n```\n```python selftest\nprint('SELFTEST OK')\n```"
    assert agents.block(t, "solution").startswith("def f")
    assert "SELFTEST" in agents.block(t, "selftest")
    assert agents.block("```python\nA=1\n```", "solution") == "A=1\n"
    assert agents.block("no code", "critic") is None


def test_ledger_roundtrip(tmp_path):
    c = ledger.connect(tmp_path / "l.sqlite")
    ledger.add_call(c, run_id="r", role="planner", attempt=1, ok=1, tokens=10, output_tokens=5, cost_usd=0.0, secs=1.0, error="")
    ledger.add_run(c, run_id="r", task="kabsch", arm="single", rep=1, model="haiku", calls=1, tokens=10, output_tokens=5,
                   cost_usd=0.0, wall_s=1.0, hidden_passed=1, hidden_total=1, all_pass=1, public_passed=3,
                   candidates_hidden=[1], notes="")
    assert ledger.done_runs(c) == {"r"}
