#!/usr/bin/env python3
"""Paging evidence: generation-only llama-bench runs with macOS vm_stat page-in deltas and a memory snapshot,
to check whether a model's weights stayed resident in RAM during the test (run under the shared GPU lock)."""
import json, re, subprocess, sys, time
from pathlib import Path
import run_experiment as X
D = Path(__file__).resolve().parent; RAW = D / "raw"
def vm():
    s = subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    g = lambda k: int(re.search(k + r":\s+(\d+)", s).group(1))
    return {"pageins": g("Pageins"), "free_pages": g("Pages free"), "wired_pages": g("Pages wired down"), "page_size": 16384}
for key in sys.argv[1:]:
    f = D / "models" / X.MODELS[key][0]
    cmd = [str(X.BIN / "llama-bench"), "-m", str(f), "-ngl", "99", "-fa", "1", "-p", "0", "-n", "128", "-r", "3", "-o", "json"]
    a = vm(); t = time.time(); r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600); b = vm()
    assert r.returncode == 0, r.stderr[-1500:]
    rows = json.loads(r.stdout)
    rec = {"command": cmd, "seconds": time.time() - t, "vm_before": a, "vm_after": b,
           "pagein_gb_during_run": (b["pageins"] - a["pageins"]) * 16384 / 1e9, "tg": rows[0]["avg_ts"], "tg_samples": rows[0]["samples_ts"],
           "busy_processes": X.others()}
    (RAW / f"paging-{key}.json").write_text(json.dumps(rec, indent=1)); print(key, round(rec["tg"], 1), "tok/s; paged in", round(rec["pagein_gb_during_run"], 1), "GB", flush=True)
