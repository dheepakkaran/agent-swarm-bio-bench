"""Shared state: one SQLite ledger for every run and every model call (experiment tracking)."""
import json, sqlite3, threading
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "results" / "ledger.sqlite"
_lock = threading.Lock()


def connect(path=DB):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(path, check_same_thread=False)
    c.executescript("""
    CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, task TEXT, arm TEXT, rep INTEGER, model TEXT,
        calls INTEGER, tokens INTEGER, output_tokens INTEGER, cost_usd REAL, wall_s REAL,
        hidden_passed INTEGER, hidden_total INTEGER, all_pass INTEGER, public_passed INTEGER,
        candidates_hidden TEXT, notes TEXT);
    CREATE TABLE IF NOT EXISTS calls(run_id TEXT, role TEXT, attempt INTEGER, ok INTEGER, tokens INTEGER,
        output_tokens INTEGER, cost_usd REAL, secs REAL, error TEXT);
    """)
    return c


def add_call(c, **kw):
    with _lock:
        c.execute("INSERT INTO calls VALUES(:run_id,:role,:attempt,:ok,:tokens,:output_tokens,:cost_usd,:secs,:error)", kw)
        c.commit()


def add_run(c, **kw):
    kw = {**kw, "candidates_hidden": json.dumps(kw.get("candidates_hidden", []))}
    with _lock:
        c.execute("INSERT OR REPLACE INTO runs VALUES(:run_id,:task,:arm,:rep,:model,:calls,:tokens,:output_tokens,"
                  ":cost_usd,:wall_s,:hidden_passed,:hidden_total,:all_pass,:public_passed,:candidates_hidden,:notes)", kw)
        c.commit()


def done_runs(c):
    return {r[0] for r in c.execute("SELECT run_id FROM runs")}
