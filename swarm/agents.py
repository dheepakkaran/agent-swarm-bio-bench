"""Headless Claude Code agents (`claude -p`, no tools): the harness executes all code."""
import json, re, subprocess, threading, time

MODEL = "haiku"
SYSTEM = ("You are a careful scientific programmer working inside a research harness. You cannot run code yourself: "
          "the harness executes what you write and reports results back. Follow the requested output format exactly.")
_slots = threading.Semaphore(6)   # at most 6 agents talking to the model at once


class AgentError(RuntimeError):
    pass


def ask(prompt, *, role, run_id, ledger, conn, need=None, timeout=300):
    """One agent turn. Retries once (recovery) if the call fails or the reply lacks the required block."""
    last = ""
    for attempt in (1, 2):
        t0 = time.time()
        try:
            with _slots:
                p = subprocess.run(["claude", "-p", "--model", MODEL, "--tools", "", "--setting-sources", "",
                                    "--no-session-persistence", "--output-format", "json", "--system-prompt", SYSTEM],
                                   input=prompt, capture_output=True, text=True, timeout=timeout)
            d = json.loads(p.stdout)
            u = d.get("usage", {})
            tok = sum(u.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"))
            text, err = d.get("result", ""), ("is_error" if d.get("is_error") else "")
            if not err and need and not block(text, need):
                err = f"missing ```python {need}``` block"
            ledger.add_call(conn, run_id=run_id, role=role, attempt=attempt, ok=int(not err), tokens=tok,
                            output_tokens=u.get("output_tokens", 0), cost_usd=d.get("total_cost_usd", 0.0),
                            secs=round(time.time() - t0, 2), error=err)
            if not err:
                return text
            last = err
        except Exception as e:
            last = f"{type(e).__name__}: {str(e)[:200]}"
            ledger.add_call(conn, run_id=run_id, role=role, attempt=attempt, ok=0, tokens=0, output_tokens=0,
                            cost_usd=0.0, secs=round(time.time() - t0, 2), error=last)
    raise AgentError(f"{role}: {last}")


def block(text, tag):
    m = re.search(r"```python[ \t]+" + re.escape(tag) + r"[^\n]*\n(.*?)```", text, re.S)
    if m:
        return m.group(1)
    if tag == "solution":   # tolerate an untagged first block
        m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
        return m.group(1) if m else None
    return None


def json_block(text):
    m = re.search(r"```(?:json)?\n(.*?)```", text, re.S)
    raw = m.group(1) if m else text
    try:
        return json.loads(raw)
    except Exception:
        return None
