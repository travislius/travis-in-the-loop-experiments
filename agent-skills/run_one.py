#!/usr/bin/env python3
"""Run one condition of the Agent Skills experiment in DeepSeek Harness.

Usage: run_one.py <cond A|B|C> <rep>
A = no expense skill (only two unrelated skills in the catalog)
B = expense-report skill, SKILL.md instructions only
C = expense-report skill, SKILL.md + bundled scripts/build_report.py
Key from env DEEPSEEK_API_KEY (never written to disk).
"""
import json, os, shutil, subprocess, sys, time, threading
from pathlib import Path
from deepseek_harness import DeepSeekHarness
HERE = Path(__file__).resolve().parent
cond, rep = sys.argv[1], int(sys.argv[2])
MODEL = os.environ.get("EXP_MODEL", "deepseek-v4-flash")
PROMPT = "Please make the October 2026 expense report from expenses.csv in this folder and save it as report.md."
run_id = f"{cond}-r{rep}"; out = HERE / "runs" / run_id
if out.exists(): shutil.rmtree(out)
ws, home = out / "workspace", out / "dsh-home"
shutil.copytree(HERE / "task" / "repo", ws); home.mkdir(parents=True)
sk = ws / ".agents" / "skills"; sk.mkdir(parents=True)
for s in (HERE / "skills" / "common").iterdir(): shutil.copytree(s, sk / s.name)
if cond in "BC": shutil.copytree(HERE / "skills" / cond / "expense-report", sk / "expense-report")
patches = [str(HERE / "patches" / p) for p in ["no-log-upload.yml", "confine.yml", "confine-approval.yml"]]
probe = subprocess.run([str(HERE / ".venv/bin/dsh"), "--profile", "sdk"] + sum([["--patch", p] for p in patches], []) + ["--dump-config"], env={**os.environ, "DSH_HOME": str(home)}, capture_output=True, text=True)
if "not found" in probe.stderr: sys.exit("PATCH_NOT_APPLIED: " + probe.stderr.strip())
events = []; t0 = time.time(); box = {}
with DeepSeekHarness(provider="deepseek-official", model=MODEL, cwd=str(ws), dsh_home=str(home), profile="sdk", patches=tuple(patches), max_tokens=32768, request_timeout_seconds=600) as h:
    th = threading.Thread(target=lambda: box.setdefault("res", h.run(PROMPT, session_id=run_id, on_notification=lambda n: events.append(n))), daemon=True)
    th.start(); th.join(600)
    fin = box["res"].finish_reason if "res" in box else "timeout"
    final = (box["res"].final_response or "")[:2000] if "res" in box else ""
wall = time.time() - t0
check = json.loads(subprocess.run([str(HERE / "agent-bin" / "python3"), str(HERE / "check.py"), str(ws), str(HERE / "task" / "truth.json")], capture_output=True, text=True).stdout or "{}")
# metrics from the harness's own session log
steps = 0; tools = {}; usage = {"input": 0, "output": 0, "cache_hit": 0}; skill_loads = []; catalog_chars = 0; script_runs = 0
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
            a = json.dumps(data)
            if n == "skill": skill_loads.append(a[:300])
            if "build_report.py" in a: script_runs += 1
        if t == "user/message" and "<system-reminder>" in json.dumps(data) and "skill" in json.dumps(data).lower(): catalog_chars = max(catalog_chars, len(json.dumps(data)))
        if t.startswith("assistant/message"):
            uu = data.get("usage") or {}
            usage["input"] += uu.get("inputTokens", uu.get("prompt_tokens", 0)) or 0
            usage["output"] += uu.get("outputTokens", uu.get("completion_tokens", 0)) or 0
            usage["cache_hit"] += uu.get("cacheReadTokens", uu.get("prompt_cache_hit_tokens", 0)) or 0
rec = {"run": run_id, "cond": cond, "rep": rep, "model": MODEL, "profile": "sdk", "prompt": PROMPT, "finish_reason": fin, "wall_seconds": round(wall, 1), "steps": steps,
       "tool_calls": tools, "skill_loads": skill_loads, "script_runs": script_runs, "catalog_message_chars": catalog_chars, "usage": usage, "check": check, "final_response": final}
json.dump(rec, open(out / "result.json", "w"), indent=1)
rp = ws / "report.md"
if rp.exists(): shutil.copy2(rp, out / "report.md")
print(json.dumps({k: rec[k] for k in ["run", "finish_reason", "wall_seconds", "tool_calls", "script_runs", "usage"]} | {"pass": check.get("pass"), "numbers": check.get("numbers_correct"), "format": check.get("house_format_exact")}), flush=True)
