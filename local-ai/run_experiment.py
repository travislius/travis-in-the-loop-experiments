#!/usr/bin/env python3
"""Local AI Explained — on-Mac experiment.

Measures, for each local GGUF model:
  * file size and bits per weight (from the file and the GGUF parameter count)
  * memory the runtime actually allocates (llama.cpp's own buffer report + macOS peak footprint)
  * prompt processing (prefill) and generation (decode) speed with llama-bench, at several context depths
  * perplexity on a fixed slice of WikiText-2 (quality check across quantizations of the same model)

Usage:  python3 run_experiment.py <stage> [model ...]
  stages: bench | memory | ppl | env
Environment:
  LLAMA_BIN   directory with llama-bench / llama-completion / llama-perplexity (built from source)
"""
import json, os, re, subprocess, sys, time, platform, datetime
from pathlib import Path

D = Path(__file__).resolve().parent
M = D / "models"
RAW = D / "raw"; RAW.mkdir(exist_ok=True)
BIN = Path(os.environ.get("LLAMA_BIN", str(Path.home() / ".hermes/cache/scratch/llama-src/build/bin")))
MODELS = {
    "flint-q4": ("Flint-Q4_K_M.gguf", "Flint 40B-A2.5B MoE", "Q4_K_M", 39.8e9, 2.5e9),
    "flint-q8": ("Flint-Q8_0.gguf", "Flint 40B-A2.5B MoE", "Q8_0", 39.8e9, 2.5e9),
    "qwen32-q4": ("Qwen3-32B-Q4_K_M.gguf", "Qwen3-32B dense", "Q4_K_M", 32.8e9, 32.8e9),
}
REPS = 3           # llama-bench repetitions per test
PROMPT = 512       # prefill test length (tokens)
GEN = 128          # decode test length (tokens)
DEPTHS = "0,8192,32768"  # context already in the KV cache before the test


def others():
    """Snapshot of other heavy processes (GPU contention is a stated limitation)."""
    out = subprocess.run(["ps", "-Ao", "pid,pcpu,rss,comm"], capture_output=True, text=True).stdout.splitlines()[1:]
    rows = []
    for l in out:
        p = l.split(None, 3)
        if len(p) == 4 and float(p[1]) > 20:
            rows.append({"pid": int(p[0]), "cpu_pct": float(p[1]), "rss_mb": int(p[2]) // 1024, "cmd": p[3][-80:]})
    return rows


def bench(key):
    f = M / MODELS[key][0]
    out = RAW / f"bench-{key}.json"
    cmd = [str(BIN / "llama-bench"), "-m", str(f), "-ngl", "99", "-fa", "1", "-p", str(PROMPT), "-n", str(GEN),
           "-d", DEPTHS, "-r", str(REPS), "-o", "json"]
    before = others(); t = time.time()
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    (RAW / f"bench-{key}.log").write_text(r.stderr)
    assert r.returncode == 0, r.stderr[-2000:]
    rows = json.loads(r.stdout)
    out.write_text(json.dumps({"command": cmd, "started": t, "seconds": time.time() - t,
                               "busy_processes_before": before, "busy_processes_after": others(), "results": rows}, indent=1))
    for x in rows:
        print(key, "pp" if x["n_prompt"] else "tg", x["n_depth"], round(x["avg_ts"], 1), "±", round(x["stddev_ts"], 1), flush=True)


def memory(key):
    """One real generation; record llama.cpp's buffer sizes and the process's peak memory footprint."""
    f = M / MODELS[key][0]
    prompt = "Write a Python function that checks whether a string is a palindrome, ignoring case and punctuation."
    cmd = ["/usr/bin/time", "-l", str(BIN / "llama-completion"), "-m", str(f), "-ngl", "99", "-fa", "on", "-c", "8192",
           "-n", "200", "--temp", "0", "--seed", "42", "-no-cnv", "-v", "-p", prompt]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    (RAW / f"memory-{key}.log").write_text(r.stderr); (RAW / f"memory-{key}.out.txt").write_text(r.stdout)
    assert r.returncode == 0, r.stderr[-2000:]
    e = r.stderr
    def mib(pat):
        return sum(float(x) for x in re.findall(pat, e))
    rec = {
        "model_buffer_mib": mib(r"model buffer size =\s*([\d.]+) MiB"),
        "kv_buffer_mib_ctx8192": mib(r"KV buffer size =\s*([\d.]+) MiB"),
        "compute_buffer_mib": mib(r"compute buffer size =\s*([\d.]+) MiB"),
        "peak_memory_footprint_bytes": int(re.search(r"(\d+)\s+peak memory footprint", e).group(1)),
        "max_rss_bytes": int(re.search(r"(\d+)\s+maximum resident set size", e).group(1)),
        "context": 8192, "prompt": prompt, "command": cmd[2:],
    }
    (RAW / f"memory-{key}.json").write_text(json.dumps(rec, indent=1)); print(key, json.dumps(rec)[:400])


def ppl(key, chunks=60):
    f = M / MODELS[key][0]
    data = D / "data/wikitext-2-raw/wiki.test.raw"
    cmd = [str(BIN / "llama-perplexity"), "-m", str(f), "-ngl", "99", "-fa", "on", "-f", str(data), "-c", "512", "--chunks", str(chunks), "-b", "512"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    (RAW / f"ppl-{key}.log").write_text(r.stderr + r.stdout)
    assert r.returncode == 0, r.stderr[-2000:]
    m = re.search(r"Final estimate: PPL = ([\d.]+) \+/- ([\d.]+)", r.stderr + r.stdout)
    rec = {"ppl": float(m.group(1)), "ppl_err": float(m.group(2)), "chunks": chunks, "ctx": 512, "dataset": "WikiText-2 raw test", "command": cmd}
    (RAW / f"ppl-{key}.json").write_text(json.dumps(rec, indent=1)); print(key, rec["ppl"], rec["ppl_err"])


def env():
    commit = subprocess.run(["git", "-C", str(BIN.parent.parent), "log", "-1", "--format=%H %cd"], capture_output=True, text=True).stdout.strip()
    hw = subprocess.run(["system_profiler", "SPHardwareDataType", "SPDisplaysDataType"], capture_output=True, text=True).stdout
    keep = [l.strip() for l in hw.splitlines() if re.search(r"Chip|Total Number of Cores|Memory:|Model Identifier|Chipset", l)]
    files = {k: {"file": v[0], "bytes": (M / v[0]).stat().st_size} for k, v in MODELS.items() if (M / v[0]).exists()}
    rec = {"date": datetime.datetime.now().astimezone().isoformat(), "macos": platform.mac_ver()[0], "hardware": keep,
           "llama_cpp_commit": commit, "files": files}
    (RAW / "env.json").write_text(json.dumps(rec, indent=1)); print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    stage, keys = sys.argv[1], sys.argv[2:] or list(MODELS)
    if stage == "env": env()
    else:
        for k in keys: {"bench": bench, "memory": memory, "ppl": ppl}[stage](k)
