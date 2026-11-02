#!/usr/bin/env python3
"""Run one DeepSeek Harness task in one mode and record metrics.

Usage: run_one.py <task> <mode> <rep>
  task: bugfix | batch     mode: minimal | standard | ptc
The API key is read from the environment (DEEPSEEK_API_KEY); it is never written to disk here.
"""
import json, os, shutil, subprocess, sys, time
from pathlib import Path
from deepseek_harness import DeepSeekHarness

HERE = Path(__file__).resolve().parent
task, mode, rep = sys.argv[1], sys.argv[2], int(sys.argv[3])
MODEL = os.environ.get("DSH_EXPERIMENT_MODEL", "deepseek-v4-flash")
run_id = f"{task}-{mode}-r{rep}"
out = HERE / "runs" / run_id
if out.exists():
    raise SystemExit(f"Refusing to overwrite recorded evidence: {out}. Use a new repetition number.")
ws, home = out / "workspace", out / "dsh-home"
shutil.copytree(HERE / "tasks" / task / "repo", ws); home.mkdir(parents=True)

profile = "sdk-minimal" if mode == "minimal" else "sdk"
patches = [str(HERE / "patches" / "no-log-upload.yml"), str(HERE / "patches" / "confine.yml")]
if mode != "minimal": patches.append(str(HERE / "patches" / "confine-approval.yml"))
if mode == "ptc": patches.append(str(HERE / "patches" / "ptc.yml"))

# Fail loudly if any patch row id does not exist in this runtime (dsh only warns and ignores it).
_probe = subprocess.run([str(HERE / ".venv/bin/dsh"), "--profile", profile] + sum([["--patch", p] for p in patches], []) + ["--dump-config"],
                        env={**os.environ, "DSH_HOME": str(home)}, capture_output=True, text=True)
if "not found" in _probe.stderr: sys.exit("PATCH_NOT_APPLIED: " + _probe.stderr.strip())
prompt = json.load(open(HERE / "tasks" / "PROMPTS.json"))[task]

events = []
t0 = time.time()
with DeepSeekHarness(provider="deepseek-official", model=MODEL, cwd=str(ws), dsh_home=str(home),
                     profile=profile, patches=tuple(patches), max_tokens=32768,
                     request_timeout_seconds=900) as h:
    import threading
    RUN_TIMEOUT = int(os.environ.get("RUN_TIMEOUT", "900"))
    box = {}
    th = threading.Thread(target=lambda: box.setdefault("res", h.run(prompt, session_id=run_id, on_notification=lambda n: events.append(n))), daemon=True)
    th.start(); th.join(RUN_TIMEOUT)
    if th.is_alive():
        class _R: finish_reason = "timeout"; final_response = f"run exceeded {RUN_TIMEOUT}s cap"
        res = _R()
    else:
        res = box["res"]
wall = time.time() - t0

# check
chk = HERE / "tasks" / task / "check.py"
extra = str(HERE / "tasks" / task / {"bugfix": "repo/tests/test_invoice.py", "calc": "SPEC-not-used"}.get(task, "truth.json"))
check = json.loads(subprocess.run([str(HERE / "agent-bin" / "python3"), str(chk), str(ws), extra], capture_output=True, text=True).stdout or "{}")

# metrics from the session log (the harness's own append-only record)
logs = list((home / "sessions").rglob("*.jsonl"))
steps = tools = 0; usage = {"input": 0, "output": 0, "cache_hit": 0}; tool_names = {}
for lf in logs:
    for line in open(lf):
        try: ev = json.loads(line)
        except Exception: continue
        t = ev.get("type", "")
        if t == "step/start": steps += 1
        if t == "tool/call":
            tools += 1; n = (ev.get("data") or ev).get("name") or (ev.get("data") or {}).get("toolName", "?"); tool_names[n] = tool_names.get(n, 0) + 1
        u = json.dumps(ev)
        if '"usage"' in u and t.startswith("assistant/message"):
            uu = (ev.get("data") or ev).get("usage") or {}
            usage["input"] += uu.get("inputTokens", uu.get("prompt_tokens", 0)) or 0
            usage["output"] += uu.get("outputTokens", uu.get("completion_tokens", 0)) or 0
            usage["cache_hit"] += uu.get("cacheReadTokens", uu.get("prompt_cache_hit_tokens", 0)) or 0
import subprocess as _sp
_hdr_tools = []
for lf in (home / "sessions").rglob("session*"):
    if lf.suffix not in (".jsonl", ".zstd"): continue
    raw = _sp.run(["zstd", "-dc", str(lf)], capture_output=True).stdout if lf.suffix == ".zstd" else lf.read_bytes()
    for line in raw.decode().splitlines():
        e = json.loads(line)
        if e.get("type") == "request/header":
            _hdr_tools = [t.get("name") for t in e["data"]["header"].get("tools", [])]; break
    if _hdr_tools: break
if mode == "ptc" and "run_code" not in _hdr_tools: sys.exit(f"PTC_NOT_ACTIVE: tools={_hdr_tools}")
rec = {"model_visible_tools": _hdr_tools, "run": run_id, "task": task, "mode": mode, "rep": rep, "model": MODEL, "profile": profile,
       "finish_reason": res.finish_reason, "wall_seconds": round(wall, 1), "steps": steps,
       "tool_calls": tools, "tool_names": tool_names, "usage": usage, "check": check,
       "session_logs": [str(p.relative_to(out)) for p in logs], "notifications": len(events),
       "final_response": (res.final_response or "")[:2000]}
json.dump(rec, open(out / "result.json", "w"), indent=1)
print(json.dumps({k: rec[k] for k in ["run", "finish_reason", "wall_seconds", "steps", "tool_calls", "usage", "check"]}))
