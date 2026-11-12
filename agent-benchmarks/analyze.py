#!/usr/bin/env python3
"""Aggregate runs/*/result.json into results.json (Agent Benchmarks Explained)."""
import json, statistics as st, datetime as dt
from pathlib import Path
H = Path(__file__).resolve().parent
EASY = ["slugify", "overlap", "lru", "money", "merge", "bucket", "roman", "semver"]; HARD = ["cron", "expr", "glob"]
# DeepSeek list prices, USD per 1M tokens (api-docs.deepseek.com/quick_start/pricing, read 2026-11-11)
PRICE = {"deepseek-flash": {"peak": (0.006, 0.3, 1.2), "off": (0.003, 0.15, 0.6)}, "deepseek-v4-pro": {"peak": (0.044, 1.32, 3.96), "off": (0.022, 0.66, 1.98)}}
def peak(t):  # peak: 01-04 and 06-10 UTC, Mon-Fri
    return t.weekday() < 5 and (1 <= t.hour < 4 or 6 <= t.hour < 10)
runs = [json.loads(p.read_text()) for p in sorted((H / "runs").glob("*/result.json"))]
for r in runs:
    t = dt.datetime.strptime(r["started_utc"], "%Y-%m-%dT%H:%M:%SZ"); hit, miss, out = PRICE[r["model"]]["peak" if peak(t) else "off"]
    u = r["usage"]; r["tariff"] = "peak" if peak(t) else "off-peak"
    r["cost_usd"] = (u["cache_hit"] * hit + u["input"] * miss + u["output"] * out) / 1e6
def summ(model, tasks):
    rs = [r for r in runs if r["model"] == model and r["task"] in tasks]
    per = {t: [r for r in rs if r["task"] == t] for t in tasks}
    k = min(len(v) for v in per.values())
    return {"model": model, "tasks": len(tasks), "attempts": len(rs), "k": k,
            "pass_at_1": sum(r["resolved"] for r in rs) / len(rs),
            "pass_at_k": sum(any(r["resolved"] for r in v) for v in per.values()) / len(tasks),
            "pass_hat_k": sum(all(r["resolved"] for r in v) for v in per.values()) / len(tasks),
            "per_task_successes": {t: sum(r["resolved"] for r in v) for t, v in per.items()},
            "median_wall_s": st.median(r["wall_seconds"] for r in rs), "median_output_tokens": st.median(r["usage"]["output"] for r in rs),
            "median_steps": st.median(r["steps"] for r in rs), "mean_cost_per_attempt_usd": st.mean(r["cost_usd"] for r in rs),
            "total_cost_usd": sum(r["cost_usd"] for r in rs),
            "cost_per_success_usd": sum(r["cost_usd"] for r in rs) / max(1, sum(r["resolved"] for r in rs)),
            "tariffs": sorted({r["tariff"] for r in rs})}
out = {"generated": dt.datetime.now().astimezone().isoformat(), "n_runs": len(runs),
       "easy": [summ(m, EASY) for m in PRICE], "hard": [summ(m, HARD) for m in PRICE] if any(r["task"] in HARD for r in runs) and all(len([r for r in runs if r["task"]==t]) for t in HARD) else [], "all": [summ(m, EASY + HARD) for m in PRICE] if all(len([r for r in runs if r["task"]==t]) for t in HARD) else [],
       "total_cost_usd": sum(r["cost_usd"] for r in runs),
       "runs": [{k: r[k] for k in ["run", "task", "model", "rep", "resolved", "hidden_tests_passed", "hidden_tests_failed", "wall_seconds", "steps", "usage", "cost_usd", "tariff", "finish_reason"]} for r in runs]}
(H / "results.json").write_text(json.dumps(out, indent=1))
for g in ["easy", "hard", "all"]:
    for s in out[g]: print(g, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}))
print("TOTAL $", round(out["total_cost_usd"], 4))
