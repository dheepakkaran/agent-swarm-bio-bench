"""Run a critic's check(f) against one candidate. Executed in a subprocess. Prints JSON."""
import importlib.util, json, sys

def load(name, path):
    s = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

critic_path, cand_path, func = sys.argv[1:4]
try:
    cand = load("candidate", cand_path)
    f = getattr(cand, func)
except Exception as e:
    print(json.dumps({"failures": [f"candidate does not load: {type(e).__name__}: {e}"]})); sys.exit(0)
try:
    critic = load("critic", critic_path)
    fails = critic.check(f)
    print(json.dumps({"failures": [str(x)[:300] for x in list(fails)[:10]]}))
except Exception as e:
    print(json.dumps({"critic_error": f"{type(e).__name__}: {str(e)[:300]}"}))
