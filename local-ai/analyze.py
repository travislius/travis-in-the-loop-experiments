#!/usr/bin/env python3
"""Aggregate raw/*.json into results.json (the single source for the video's charts and narration numbers)."""
import json, re
from pathlib import Path
D = Path(__file__).resolve().parent; RAW = D / "raw"
import run_experiment as X
env = json.loads((RAW / "env.json").read_text())
out = {"date": env["date"], "hardware": env["hardware"], "macos": env["macos"], "llama_cpp_commit": env["llama_cpp_commit"],
       "ram_gb": 64, "bandwidth_gbs": 614, "bandwidth_source": "Apple newsroom, Mar 3 2026 (M5 Max 40-core GPU: up to 614GB/s)",
       "flint_bf16_file_gb": 79.63, "flint_bf16_source": "ggml-org/Flint-GGUF Flint-BF16.gguf size (HF API)",
       "reps": X.REPS, "prompt_tokens": X.PROMPT, "gen_tokens": X.GEN, "depths": X.DEPTHS, "models": {}}
for k, (f, name, quant, params, active) in X.MODELS.items():
    m = {"file": f, "name": name, "quant": quant, "params_nominal": params, "active_nominal": active}
    b = json.loads((RAW / f"bench-{k}.json").read_text())
    rows = b["results"]
    m["model_n_params"] = rows[0]["model_n_params"]; m["file_bytes"] = (D / "models" / f).stat().st_size
    m["bits_per_weight"] = m["file_bytes"] * 8 / m["model_n_params"]
    m["tg"] = {str(x["n_depth"]): {"avg": x["avg_ts"], "sd": x["stddev_ts"], "samples": x["samples_ts"]} for x in rows if x["n_gen"]}
    m["pp"] = {str(x["n_depth"]): {"avg": x["avg_ts"], "sd": x["stddev_ts"], "samples": x["samples_ts"]} for x in rows if x["n_prompt"]}
    m["busy_processes"] = b["busy_processes_before"] + b["busy_processes_after"]
    mm = json.loads((RAW / f"memory-{k}.json").read_text()); m["memory"] = mm
    # bytes actually streamed per generated token (weights only, upper-bound style estimate)
    m["est_weight_gb_read_per_token"] = active * m["bits_per_weight"] / 8 / 1e9
    m["effective_gbs_at_depth0"] = m["est_weight_gb_read_per_token"] * m["tg"]["0"]["avg"]
    p = RAW / f"ppl-{k}.json"
    if p.exists(): m["ppl"] = json.loads(p.read_text())
    out["models"][k] = m
(D / "results.json").write_text(json.dumps(out, indent=1))
for k, m in out["models"].items():
    print(k, f'{m["file_bytes"]/1e9:.2f}GB {m["bits_per_weight"]:.2f}bpw', 'tg', {d: round(v["avg"], 1) for d, v in m["tg"].items()}, 'pp', {d: round(v["avg"]) for d, v in m["pp"].items()},
          'mem', round(m["memory"]["model_buffer_mib"] / 1024, 2), 'GiB kv8k', m["memory"]["kv_buffer_mib_ctx8192"], 'peak', round(m["memory"]["peak_memory_footprint_bytes"] / 2**30, 2),
          'eff', round(m["effective_gbs_at_depth0"]), m.get("ppl", {}).get("ppl"))
