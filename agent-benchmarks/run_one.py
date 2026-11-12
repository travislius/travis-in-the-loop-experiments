#!/usr/bin/env python3
"""One agent attempt at one bug-fix task (Agent Benchmarks Explained, 2026-11).

Usage: run_one.py <task> <model> <rep>
The agent sees only the buggy repo + ISSUE.md. Scoring runs hidden_test.py
afterwards (the agent never sees it). Key from env DEEPSEEK_API_KEY.
"""
import json, os, shutil, subprocess, sys, time, threading
from pathlib import Path
from deepseek_harness import DeepSeekHarness
HERE = Path(__file__).resolve().parent
task, model, rep = sys.argv[1], sys.argv[2], int(sys.argv[3])
PROMPT = "There is a bug report in ISSUE.md. Fix the code in this folder so the issue is resolved. Do not ask questions; make the fix."
short = {"deepseek-flash": "flash", "deepseek-v4-pro": "pro"}[model]
run_id = f"{task}-{short}-r{rep}"; out = HERE / "runs" / run_id
if out.exists(): shutil.rmtree(out)
ws, home = out / "workspace", out / "dsh-home"
shutil.copytree(HERE / "tasks" / task / "repo", ws); home.mkdir(parents=True)
patches = [str(HERE / "patches" / p) for p in ["no-log-upload.yml", "confine.yml", "confine-approval.yml"]]
events = []; t0 = time.time(); box = {}
with DeepSeekHarness(provider="deepseek-official", model=model, cwd=str(ws), dsh_home=str(home), profile="sdk", patches=tuple(patches), max_tokens=32768, request_timeout_seconds=600) as h:
    th = threading.Thread(target=lambda: box.setdefault("res", h.run(PROMPT, session_id=run_id, on_notification=lambda n: events.append(n))), daemon=True)
    th.start(); th.join(900)
    fin = box["res"].finish_reason if "res" in box else "timeout"
    final = (box["res"].final_response or "")[:1500] if "res" in box else ""
wall = time.time() - t0
# hidden tests, run in a scratch copy so the agent's own files can't interfere
chk = out / "check"; shutil.copytree(ws, chk, ignore=shutil.ignore_patterns(".agents", "__pycache__", ".pytest_cache"))
shutil.copy2(HERE / "tasks" / task / "hidden_test.py", chk / "test_hidden_zz.py")
r = subprocess.run([str(HERE / ".venv/bin/python"), "-m", "pytest", "-q", "-p", "no:cacheprovider", "test_hidden_zz.py"], cwd=chk, capture_output=True, text=True, timeout=120)
last = (r.stdout.strip().splitlines() or [""])[-1]
import re
npass = int((re.search(r"(\d+) passed", last) or [0, 0])[1]); nfail = int((re.search(r"(\d+) failed", last) or [0, 0])[1]) + int((re.search(r"(\d+) error", last) or [0, 0])[1])
shutil.rmtree(chk)
steps = 0; tools = {}; usage = {"input": 0, "output": 0, "cache_hit": 0}
for lf in (home / "sessions").rglob("session*"):
    if lf.suffix not in (".jsonl", ".zstd"): continue
    raw = subprocess.run(["zstd", "-dc", str(lf)], capture_output=True).stdout if lf.suffix == ".zstd" else lf.read_bytes()
    for line in raw.decode().splitlines():
        try: ev = json.loads(line)
        except Exception: continue
        t = ev.get("type", ""); data = ev.get("data") or {}
        if t == "step/start": steps += 1
        if t == "tool/call":
            n = data.get("name") or data.get("toolName", "?"); tools[n] = tools.get(n, 0) + 1
        if t.startswith("assistant/message"):
            uu = data.get("usage") or {}
            usage["input"] += uu.get("inputTokens", uu.get("prompt_tokens", 0)) or 0
            usage["output"] += uu.get("outputTokens", uu.get("completion_tokens", 0)) or 0
            usage["cache_hit"] += uu.get("cacheReadTokens", uu.get("prompt_cache_hit_tokens", 0)) or 0
rec = {"run": run_id, "task": task, "model": model, "rep": rep, "prompt": PROMPT, "finish_reason": fin, "wall_seconds": round(wall, 1), "steps": steps,
       "tool_calls": tools, "usage": usage, "hidden_tests_passed": npass, "hidden_tests_failed": nfail, "resolved": nfail == 0 and npass > 0, "pytest_summary": last, "final_response": final,
       "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0))}
json.dump(rec, open(out / "result.json", "w"), indent=1)
subprocess.run(["diff", "-ru", str(HERE / "tasks" / task / "repo"), str(ws)], stdout=open(out / "patch.diff", "w"))
print(json.dumps({k: rec[k] for k in ["run", "finish_reason", "wall_seconds", "steps", "usage", "resolved", "pytest_summary"]}), flush=True)
