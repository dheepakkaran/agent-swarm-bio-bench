"""Run the experiment: tasks × arms × reps, every arm capped at the same number of model calls.

    python -m swarm.run --reps 3            # all runs not yet in the ledger
    python -m swarm.run --task kabsch --arm swarm --reps 1
"""
import argparse, json, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from swarm import agents, ledger
from tasks import common

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "results" / "runs"
ARMS = ["single", "swarm", "swarm_nocritic"]
CALL_CAP = 6
FORMAT = """Write the function in pure Python 3.12. The standard library and numpy are allowed; no other imports (no Biopython).
Reply with exactly two fenced code blocks:
```python solution
# a module that defines {func}
```
```python selftest
# a script that does `from solution import {func}`, asserts results you are certain of (include edge cases),
# and prints SELFTEST OK at the end
```"""
DEFAULT_APPROACHES = ["a direct dynamic-programming or closed-form implementation that follows the spec literally",
                      "an implementation built around the trickiest edge cases first",
                      "an alternative formulation (different recurrence or decomposition) of the same method"]


# ---------- harness actions (the harness executes, agents only write) ----------
def save(d, name, text):
    d.mkdir(parents=True, exist_ok=True); (d / name).write_text(text or ""); return d / name


def run_selftest(cdir, timeout=60):
    if not (cdir / "selftest.py").exists():
        return False, "no selftest"
    try:
        p = subprocess.run([sys.executable, "-E", "-s", "selftest.py"], cwd=cdir, capture_output=True, text=True, timeout=timeout)
        ok = p.returncode == 0 and "SELFTEST OK" in p.stdout
        return ok, "" if ok else (p.stderr or p.stdout)[-600:]
    except subprocess.TimeoutExpired:
        return False, f"selftest timeout after {timeout}s"


def run_critic(critic_path, cdir, func, timeout=90):
    try:
        p = subprocess.run([sys.executable, "-I", str(ROOT / "tasks" / "_critic_runner.py"), str(critic_path),
                            str(cdir / "solution.py"), func], capture_output=True, text=True, timeout=timeout)
        d = json.loads(p.stdout.strip().splitlines()[-1])
    except subprocess.TimeoutExpired:
        return [f"timeout after {timeout}s on the critic's checks"], ""
    except Exception as e:
        return [], f"critic runner: {type(e).__name__}"
    return d.get("failures", []), d.get("critic_error", "")


class Candidate:
    def __init__(self, cdir, task):
        self.dir, self.task = cdir, task
        self.code = (cdir / "solution.py").read_text()
        t = common.load(task)
        self.pub_passed, self.pub_total, self.pub_fails = common.evaluate(task, cdir / "solution.py", t.public())
        self.self_ok, self.self_msg = run_selftest(cdir)
        self.critic_fails, self.critic_err = [], ""

    def key(self, use_critic):
        return (self.pub_passed, -len(self.critic_fails)) if use_critic else (self.pub_passed, int(self.self_ok))

    def evidence(self, use_critic):
        ev = [f"public example failed: {f}" for f in self.pub_fails]
        if use_critic:
            ev += [f"critic check failed: {f}" for f in self.critic_fails]
        elif not self.self_ok:
            ev.append(f"your selftest failed: {self.self_msg}")
        return ev


def write_candidate(text, cdir):
    save(cdir, "solution.py", agents.block(text, "solution"))
    st = agents.block(text, "selftest")
    if st: save(cdir, "selftest.py", st)
    save(cdir, "reply.md", text)


# ---------- agent roles ----------
class Run:
    def __init__(self, task, arm, rep, conn):
        self.task, self.arm, self.rep, self.conn = task, arm, rep, conn
        self.id = f"{task}-{arm}-r{rep}"
        self.dir = RUNS / self.id
        self.spec = common.spec(task)
        self.func = common.load(task).FUNC
        self.calls = 0

    def ask(self, prompt, role, need=None):
        if self.calls >= CALL_CAP:
            raise agents.AgentError("call cap reached")
        self.calls += 1
        save(self.dir / "prompts", f"{self.calls:02d}-{role}.md", prompt)
        return agents.ask(prompt, role=role, run_id=self.id, ledger=ledger, conn=self.conn, need=need)

    def implement(self, role, cdir, hint=""):
        text = self.ask(f"{self.spec}\n{hint}\n{FORMAT.format(func=self.func)}", role, need="solution")
        write_candidate(text, cdir)
        return Candidate(cdir, self.task)

    def refine(self, cand, evidence, cdir, role):
        ev = "\n".join(f"- {e}" for e in evidence[:12])
        prompt = (f"{self.spec}\nCurrent implementation:\n```python\n{cand.code}\n```\n"
                  f"The harness executed checks and reported these failures (a checker can be wrong too; decide which are real):\n{ev}\n\n"
                  f"Reply with the corrected module.\n{FORMAT.format(func=self.func)}")
        text = self.ask(prompt, role, need="solution")
        write_candidate(text, cdir)
        return Candidate(cdir, self.task)

    def plan(self):
        prompt = (f"{self.spec}\nYou are the planner of a team of 3 implementers. Do not write the solution. "
                  "Reply with one ```json block: {\"pitfalls\": [up to 6 short strings], "
                  "\"approaches\": [3 different implementation approaches, one per implementer]}.")
        d = agents.json_block(self.ask(prompt, "planner")) or {}
        ap = [a for a in d.get("approaches", []) if isinstance(a, str)][:3]
        ap += DEFAULT_APPROACHES[len(ap):]
        pit = [p for p in d.get("pitfalls", []) if isinstance(p, str)][:6]
        save(self.dir, "plan.json", json.dumps({"pitfalls": pit, "approaches": ap}, indent=1))
        return ap, pit

    def implement_team(self, approaches, pitfalls):
        pit = "\n".join(f"- {p}" for p in pitfalls)
        hints = [f"\nTeam plan. Known pitfalls:\n{pit}\nYour assigned approach: {a}\n" for a in approaches]
        with ThreadPoolExecutor(3) as ex:   # the three implementers work in parallel
            futs = [ex.submit(self.implement, f"implementer{i+1}", self.dir / f"cand{i+1}", h) for i, h in enumerate(hints)]
            out = []
            for f in futs:
                try: out.append(f.result())
                except agents.AgentError: pass
        return out

    def critic(self, cands):
        shown = "\n\n".join(f"Candidate {i+1}:\n```python\n{c.code}\n```" for i, c in enumerate(cands))
        prompt = (f"{self.spec}\nYou are the critic. Candidates from the team:\n{shown}\n\n"
                  "Do not fix them. Write an independent checker that any candidate function can be tested with. "
                  "Use methods that do not share the candidates' logic: brute force on small inputs, invariants "
                  "(symmetry, bounds, invariance under transformations), and hand-computed cases incl. edge cases.\n"
                  "Reply with one block:\n```python critic\n# numpy + standard library only\n"
                  "def check(f):\n    \"\"\"Call f on many inputs. Return a list (max 10) of failure strings that show the input, "
                  "the returned value and what was expected; return [] if everything passes.\"\"\"\n```")
        text = self.ask(prompt, "critic", need="critic")
        path = save(self.dir, "critic.py", agents.block(text, "critic"))
        for c in cands:
            c.critic_fails, c.critic_err = run_critic(path, c.dir, self.func)
        return path

    # ---------- arms ----------
    def single(self):
        best = cur = self.implement("implementer", self.dir / "cand1")
        hist = [best]
        while self.calls < CALL_CAP and best.evidence(False):
            try: cur = self.refine(best, best.evidence(False), self.dir / f"cand{self.calls+1}", "refiner")
            except agents.AgentError: break
            hist.append(cur)
            if cur.key(False) >= best.key(False): best = cur
        return best, hist

    def swarm(self, use_critic=True):
        ap, pit = self.plan()
        cands = self.implement_team(ap, pit)
        if not cands:
            raise agents.AgentError("no implementer produced code")
        hist = list(cands)
        crit = None
        if use_critic:
            try: crit = self.critic(cands)
            except agents.AgentError: pass
        best = max(cands, key=lambda c: c.key(use_critic))
        refines = 1 if use_critic else 2
        for r in range(refines):
            ev = best.evidence(use_critic)
            if not ev or self.calls >= CALL_CAP: break
            try: new = self.refine(best, ev, self.dir / f"refine{r+1}", "refiner")
            except agents.AgentError: break
            if crit:
                new.critic_fails, new.critic_err = run_critic(crit, new.dir, self.func)
            hist.append(new)
            if new.key(use_critic) >= best.key(use_critic): best = new
        return best, hist

    def execute(self):
        t0 = time.time(); notes = ""
        try:
            best, hist = {"single": self.single, "swarm": lambda: self.swarm(True),
                          "swarm_nocritic": lambda: self.swarm(False)}[self.arm]()
        except agents.AgentError as e:
            best, hist, notes = None, [], str(e)
        wall = time.time() - t0
        t = common.load(self.task)
        hidden = t.hidden()
        if best:
            hp, ht, hf = common.evaluate(self.task, best.dir / "solution.py", hidden)
            save(self.dir, "final_failures.txt", "\n".join(hf))
            save(self.dir, "final_solution.py", best.code)
        else:
            hp, ht = 0, len(hidden)
        cand_hidden = [common.evaluate(self.task, c.dir / "solution.py", hidden)[0] for c in hist]
        rows = self.conn.execute("SELECT SUM(tokens), SUM(output_tokens), SUM(cost_usd), COUNT(*) FROM calls WHERE run_id=?",
                                 (self.id,)).fetchone()
        ledger.add_run(self.conn, run_id=self.id, task=self.task, arm=self.arm, rep=self.rep, model=agents.MODEL,
                       calls=self.calls, tokens=rows[0] or 0, output_tokens=rows[1] or 0, cost_usd=rows[2] or 0.0,
                       wall_s=round(wall, 1), hidden_passed=hp, hidden_total=ht, all_pass=int(hp == ht),
                       public_passed=best.pub_passed if best else 0, candidates_hidden=cand_hidden, notes=notes)
        print(f"{self.id:28s} hidden {hp}/{ht}  calls {self.calls}  {wall:5.0f}s  {notes}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", choices=common.TASKS); ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--reps", type=int, default=3); ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    conn = ledger.connect(); done = ledger.done_runs(conn)
    todo = [(t, arm, r) for r in range(1, a.reps + 1) for t in ([a.task] if a.task else common.TASKS)
            for arm in ([a.arm] if a.arm else ARMS) if f"{t}-{arm}-r{r}" not in done]
    print(f"{len(todo)} runs to do ({len(done)} already in the ledger)", flush=True)
    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(lambda x: Run(*x, conn).execute(), todo))


if __name__ == "__main__":
    main()
