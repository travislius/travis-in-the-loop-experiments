#!/usr/bin/env python3
"""Recompute per-run metrics from each run's own DeepSeek Harness session log, then aggregate.

Reads both flattened archived logs and fresh SDK run logs (zstd via the `zstd` CLI).
Writes recomputed-results.json, preserving the original results.json.
"""
import json, statistics, subprocess, sys, re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read_log(path):
    raw = subprocess.run(["zstd", "-dc", str(path)], capture_output=True).stdout if path.suffix == ".zstd" else path.read_bytes()
    for line in raw.decode("utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def metrics(run_dir):
    logs = [p for p in run_dir.rglob("session*.jsonl*") if p.suffix in (".jsonl", ".zstd")]
    if len(logs) != 1:
        raise ValueError(f"Expected exactly one session log for {run_dir.name}, got {len(logs)}")
    steps = model_calls = inner_calls = shell_hangs = 0
    tools = Counter()
    usage = Counter()
    first_req_tools = None
    for lf in logs:
        events = list(read_log(lf))
        shell_hangs += sum(json.dumps(e).count("timed out after 300") for e in events)
        for ev in events:
            t = ev.get("type")
            d = ev.get("data") or {}
            if t == "step/start":
                steps += 1
            elif t == "assistant/message":
                model_calls += 1
                u = d.get("usage") or {}
                for k in ("inputTokens", "outputTokens", "cacheReadTokens", "cacheWriteTokens", "totalTokens"):
                    usage[k] += u.get(k) or 0
                for block in (d.get("message") or {}).get("content", []):
                    if block.get("type") == "tool-call":
                        tools[block.get("name")] += 1
                        if block.get("name") == "run_code":
                            inner_calls += len(re.findall(r"tools\.\w+\(", json.loads(block["arguments"])["code"]))
            elif t == "request/header" and first_req_tools is None:
                h = json.dumps(d)
                first_req_tools = h.count('"name"')  # rough count of declared tool schemas
    return {"log_files": len(logs), "steps": steps, "model_calls": model_calls,
            "tool_calls": sum(tools.values()), "tool_calls_effective": inner_calls if tools.get("run_code") else sum(tools.values()),
            "shell_hangs_300s": shell_hangs, "tools": dict(tools), "usage": dict(usage)}


def main():
    rows = []
    for rd in sorted((HERE / "runs").iterdir()):
        rj = rd / "result.json"
        if not rj.exists():
            continue
        r = json.load(open(rj))
        if r.get("rep", 0) == 0:
            continue  # pilot run, excluded from the matrix
        m = metrics(rd)
        ok = r["check"].get("ok") if "ok" in r["check"] else (r["check"].get("visible_tests_pass") and r["check"].get("hidden_pass") == r["check"].get("hidden_total") and r["check"].get("tests_unchanged"))
        prompt_tok = m["usage"].get("inputTokens", 0) + m["usage"].get("cacheReadTokens", 0)
        rows.append({"run": r["run"], "task": r["task"], "mode": r["mode"], "rep": r["rep"], "model": r["model"],
                     "finish_reason": r["finish_reason"], "success": bool(ok) and r["finish_reason"] == "completed", "partial": r["check"].get("hidden_pass", r["check"].get("fields")), "partial_total": r["check"].get("hidden_total", r["check"].get("fields_total")), "wall_seconds": r["wall_seconds"], **m,
                     "prompt_tokens": prompt_tok,
                     "cache_hit_rate": round(m["usage"].get("cacheReadTokens", 0) / prompt_tok, 3) if prompt_tok else None})
    groups = defaultdict(list)
    for r in rows:
        groups[(r["task"], r["mode"])].append(r)
    summary = []
    for (task, mode), g in sorted(groups.items()):
        med = lambda k: statistics.median([x[k] for x in g])
        summary.append({"task": task, "mode": mode, "runs": len(g), "success": f"{sum(x['success'] for x in g)}/{len(g)}",
                        "median_wall_s": med("wall_seconds"), "median_model_calls": med("model_calls"),
                        "median_tool_calls": med("tool_calls"), "median_tool_calls_effective": med("tool_calls_effective"),
                        "shell_hangs_300s": sum(x["shell_hangs_300s"] for x in g),
                        "median_prompt_tokens": med("prompt_tokens"),
                        "median_output_tokens": statistics.median([x["usage"].get("outputTokens", 0) for x in g]),
                        "median_cache_hit_rate": statistics.median([x["cache_hit_rate"] or 0 for x in g])})
    json.dump({"runs": rows, "summary": summary}, open(HERE / "recomputed-results.json", "w"), indent=1)
    print(f"{'task':7} {'mode':9} {'ok':5} {'wall':>6} {'calls':>5} {'tools':>5} {'prompt_tok':>10} {'out_tok':>7} {'cache':>6}")
    for s in summary:
        print(f"{s['task']:7} {s['mode']:9} {s['success']:5} {s['median_wall_s']:6.1f} {s['median_model_calls']:5} {s['median_tool_calls']:5} {s['median_prompt_tokens']:10} {s['median_output_tokens']:7} {s['median_cache_hit_rate']:6.2f}")


if __name__ == "__main__":
    main()
