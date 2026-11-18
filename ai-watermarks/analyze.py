#!/usr/bin/env python3
"""Summarize raw_runs.jsonl -> results.json (+ sample-highlight.json for the video).
The run was planned for 40 prompts; it is summarized over the first N completed prompts (fixed topic order,
no selection) because local generation shared the GPU with TTS jobs. Usage: analyze.py [N]"""
import json, sys, math, statistics as st, time
from pathlib import Path
D = Path(__file__).resolve().parent
rows = [json.loads(l) for l in (D / "raw_runs.jsonl").read_text().splitlines() if l.strip()]
N = int(sys.argv[1]) if len(sys.argv) > 1 else len(rows); rows = rows[:N]; assert len(rows) == N
conds = ["human", "plain", "watermarked", "paraphrased", "edited30", "translated_roundtrip"]
summ = {}
for c in conds:
    zs = [r["detect"][c]["z"] for r in rows]
    summ[c] = {"n": N, "mean_z": st.mean(zs), "median_z": st.median(zs), "min_z": min(zs), "max_z": max(zs), "sd_z": st.stdev(zs),
               "flag_rate": sum(r["detect"][c]["flag"] for r in rows) / N, "flagged": sum(r["detect"][c]["flag"] for r in rows),
               "mean_green_frac": st.mean(r["detect"][c]["green_frac"] for r in rows), "mean_tokens": st.mean(r["detect"][c]["tokens"] for r in rows), "z": zs}
pz = {c: {} for c in ("watermarked", "plain", "human")}
for c in pz:
    for L in ("10", "25", "50", "100"):
        v = [r["prefix_z"][c][L] for r in rows if r["prefix_z"][c].get(L) is not None]
        pz[c][L] = st.mean(v) if v else None
        pz[c][L + "_flag_rate"] = (sum(x > 4 for x in v) / len(v)) if v else None
        pz[c][L + "_n"] = len(v)
res = {"model": "Qwen/Qwen2.5-1.5B-Instruct", "device": "mps (Apple silicon)", "gamma": 0.25, "delta": 2.0, "temperature": 0.7, "max_new_tokens": 200, "z_threshold": 4.0,
       "n_prompts": N, "n_planned": 40, "stopping_note": ("all planned prompts completed" if N == 40 else "summarized over the first N prompts in fixed topic order"),
       "seeding": "keyed integer hash of (secret key, previous token id, candidate id) < gamma (context width 1)",
       "paraphraser": "same model, no watermark", "translation_attack": "EN->FR->EN with the same model, no watermark", "edit_attack": "30% of words replaced by random words from the human pool",
       "human_source": "wikitext-2-raw-v1 test split (Wikipedia), first 150 words of random long paragraphs", "conditions": summ, "prefix_mean_z": pz,
       "summarized_at": time.strftime("%Y-%m-%d %H:%M %Z")}
(D / "results.json").write_text(json.dumps(res, indent=1))
# token-level highlight of one real watermarked sample (median-z watermarked row) for the video
from transformers import AutoTokenizer
import importlib.util, torch
tok = AutoTokenizer.from_pretrained(res["model"])
src = (D / "watermark.py").read_text(); ns = {"torch": torch, "V": 151936, "GAMMA": 0.25, "KEY": 15485863}
exec(src[src.index("_ARANGE = None"):src.index("def generate(")], ns)
srt = sorted(rows, key=lambda r: r["detect"]["watermarked"]["z"]); row = srt[len(srt) // 2]
text = row["texts"]["watermarked"]; ids = tok(text, add_special_tokens=False)["input_ids"]
toks = [(tok.decode([ids[0]]), False)] + [(tok.decode([ids[i]]), bool(ns["green_mask"](ids[i - 1])[ids[i]])) for i in range(1, len(ids))]
cut = toks[:110]
g = sum(x[1] for x in toks[1:])
(D / "sample-highlight.json").write_text(json.dumps({"topic": row["topic"], "row": row["i"], "tokens": cut + ([("…", False)] if len(toks) > 110 else []), "tokens_n": len(ids) - 1, "green": g,
    "z": row["detect"]["watermarked"]["z"]}, indent=1))
print(json.dumps({c: {k: round(v, 3) if isinstance(v, float) else v for k, v in s.items() if k != "z"} for c, s in summ.items()}, indent=1)); print(json.dumps(pz, indent=1))
