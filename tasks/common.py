"""Task registry + safe execution of candidate code (subprocess, timeout)."""
import importlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = ["alignment", "kabsch", "nussinov"]


def load(name):
    return importlib.import_module(f"tasks.{name}.task")


def spec(name):
    return (ROOT / name / "spec.md").read_text()


def run_candidate(code_path, func, inputs, timeout=60):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(inputs, f)
    try:
        p = subprocess.run([sys.executable, "-I", str(ROOT / "_runner.py"), str(code_path), func, f.name],
                           capture_output=True, text=True, timeout=timeout)
        data = json.loads(p.stdout.strip().splitlines()[-1]) if p.stdout.strip() else {"load_error": p.stderr[-300:]}
    except subprocess.TimeoutExpired:
        data = {"load_error": f"timeout after {timeout}s"}
    except Exception as e:
        data = {"load_error": f"{type(e).__name__}: {e}"}
    finally:
        Path(f.name).unlink(missing_ok=True)
    return data


def evaluate(name, code_path, cases, timeout=60):
    """cases = list of args. Returns (passed, total, failures[str])."""
    t = load(name)
    data = run_candidate(code_path, t.FUNC, cases, timeout)
    if "load_error" in data:
        return 0, len(cases), [f"could not run: {data['load_error']}"]
    passed, fails = 0, []
    for args, r in zip(cases, data["results"]):
        if not r["ok"]:
            fails.append(f"{t.show(args)} -> raised {r['err']}"); continue
        ok, msg = t.check(args, r["out"])
        if ok: passed += 1
        else: fails.append(f"{t.show(args)} -> {msg}")
    return passed, len(cases), fails
