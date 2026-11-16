"""Run one function from a candidate file on a list of inputs. Prints JSON. Executed in a subprocess."""
import importlib.util, json, sys, traceback

path, func, inputs = sys.argv[1], sys.argv[2], json.load(open(sys.argv[3]))
out = []
try:
    spec = importlib.util.spec_from_file_location("candidate", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    f = getattr(mod, func)
except Exception as e:
    print(json.dumps({"load_error": f"{type(e).__name__}: {e}"})); sys.exit(0)
for args in inputs:
    try:
        r = f(*args)
        if hasattr(r, "tolist"): r = r.tolist()
        if isinstance(r, tuple): r = list(r)
        out.append({"ok": True, "out": r})
    except Exception as e:
        out.append({"ok": False, "err": f"{type(e).__name__}: {str(e)[:200]}"})
print(json.dumps({"results": out}, default=float))
