#!/usr/bin/env python3
"""Minimal green-list text watermark (Kirchenbauer et al. 2023, "soft" variant) on a small open model.

Generation: before sampling each token, the previous token id + a secret key seed an RNG that splits the
vocabulary into a GREEN list (fraction GAMMA) and a red list; DELTA is added to the logits of green tokens.
Detection: re-tokenize the text, recompute each position's green list from the key, count green hits and
compute z = (hits - GAMMA*T) / sqrt(T*GAMMA*(1-GAMMA)). No model is needed for detection, only the key.

Conditions measured (same prompts):
  human        - human-written Wikipedia text (wikitext-103 test), never touched by the model
  plain        - model output without watermark
  watermarked  - model output with watermark
  paraphrased  - watermarked output rewritten by the same model WITHOUT watermark
  edited30     - watermarked output with 30% of its words replaced by random words from the human pool
  translated_roundtrip - watermarked output translated to French and back by the same model WITHOUT watermark
Also: z-score on the first 10/25/50/100 tokens (length dependence).
Usage: python watermark.py [n_prompts]
"""
import json, sys, time, random, hashlib, math, re
from pathlib import Path
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

D = Path(__file__).resolve().parent
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
GAMMA, DELTA, KEY = 0.25, 2.0, 15485863          # green fraction, logit bias, secret key
TEMP, NEW_TOKENS, Z_THRESHOLD = 0.7, 200, 4.0
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
dev = "mps" if torch.backends.mps.is_available() else "cpu"
tok = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.float16).to(dev).eval()
V = model.config.vocab_size

_ARANGE = None
def green_mask(prev_id):
    """Keyed pseudo-random split of the vocabulary, seeded by (secret key, previous token id).
    Vectorized integer hash (splitmix64-style) of (key, prev, candidate) -> uniform in [0,1); green if < GAMMA."""
    global _ARANGE
    if _ARANGE is None: _ARANGE = torch.arange(V, dtype=torch.int64)
    M = (1 << 62) - 1
    s0 = ((int(prev_id) * 0x85EBCA77 + KEY) * 0xC2B2AE3D) & M
    x = (_ARANGE * 0x9E3779B1 + s0) & M
    x = (x ^ (x >> 29)) * 0x94D049BB & M
    x = (x ^ (x >> 32)) * 0x2545F491 & M
    x = x ^ (x >> 29)
    return (x % 100000) < int(GAMMA * 100000)

def generate(messages, watermark, seed):
    torch.manual_seed(seed)
    ids = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt", return_dict=True)["input_ids"].to(dev)
    out, past, cur = [], None, ids
    with torch.no_grad():
        for _ in range(NEW_TOKENS):
            o = model(cur, past_key_values=past, use_cache=True); past = o.past_key_values
            logits = o.logits[0, -1].float().cpu()[:V]
            if watermark:
                prev = (out[-1] if out else int(ids[0, -1]))
                logits[green_mask(prev)] += DELTA
            nxt = int(torch.multinomial(torch.softmax(logits / TEMP, -1), 1))
            if nxt in (tok.eos_token_id, tok.convert_tokens_to_ids("<|im_end|>")): break
            out.append(nxt); cur = torch.tensor([[nxt]], device=dev)
    return tok.decode(out, skip_special_tokens=True).strip()

def prefix_z(text, L):
    ids = tok(text, add_special_tokens=False)["input_ids"][: L + 1]
    T = len(ids) - 1
    if T < L: return None
    hits = sum(int(green_mask(ids[i - 1])[ids[i]]) for i in range(1, len(ids)))
    return (hits - GAMMA * T) / math.sqrt(T * GAMMA * (1 - GAMMA))

def detect(text):
    ids = tok(text, add_special_tokens=False)["input_ids"]
    T = len(ids) - 1
    if T < 1: return {"tokens": 0, "green": 0, "z": 0.0}
    hits = sum(int(green_mask(ids[i - 1])[ids[i]]) for i in range(1, len(ids)))
    z = (hits - GAMMA * T) / math.sqrt(T * GAMMA * (1 - GAMMA))
    return {"tokens": T, "green": hits, "green_frac": hits / T, "z": z, "flag": z > Z_THRESHOLD}

TOPICS = ["why the sky is blue", "how bread rises", "the history of the bicycle", "how vaccines train the immune system",
 "why cats purr", "how a refrigerator works", "the causes of ocean tides", "how coffee is roasted", "why leaves change color",
 "how GPS finds your location", "the life cycle of a star", "how bees make honey", "why we dream", "how a bill becomes law",
 "the invention of the printing press", "how solar panels make electricity", "why the Roman Empire fell", "how earthquakes happen",
 "how credit scores work", "the rules of chess for beginners", "how airplanes stay in the air", "why music gives us chills",
 "how glaciers carve valleys", "the benefits of walking every day", "how the internet routes a message", "how to care for a houseplant",
 "why some people are left-handed", "how rainbows form", "how electric cars charge", "the history of the Olympic Games",
 "how batteries store energy", "why onions make you cry", "how a camera lens focuses", "how recycling is sorted",
 "why the Moon has phases", "how the heart pumps blood", "how a volcano erupts", "how sourdough starter works",
 "why exercise improves mood", "how lighthouses guided ships"]
assert N <= len(TOPICS)

def human_pool(n):
    from datasets import load_dataset  # optional; falls back to cached parquet
    raise ImportError
def load_human(n):
    import glob, pyarrow.parquet as pq
    files = sorted(glob.glob(str(Path.home() / ".cache/huggingface/hub/datasets--Salesforce--wikitext/snapshots/*/wikitext-2-raw-v1/test-*.parquet")))
    rows = [r for r in pq.read_table(files[0]).column("text").to_pylist() if len(r.split()) > 120 and not r.strip().startswith("=")]
    random.Random(7).shuffle(rows)
    return [re.sub(r" @(.)@ ", r"\1", " ".join(r.split()[:150])).replace(" ,", ",").replace(" .", ".") for r in rows[:n]]

def edit(text, pool_words, frac, rng):
    w = text.split(); idx = rng.sample(range(len(w)), int(frac * len(w)))
    for i in idx: w[i] = rng.choice(pool_words)
    return " ".join(w)

if __name__ == "__main__":
    t0 = time.time(); rows = []; rng = random.Random(42)
    human = load_human(N); pool = " ".join(human).split()
    for i, topic in enumerate(TOPICS[:N]):
        msg = [{"role": "user", "content": f"Write one informative paragraph (about 150 words) explaining {topic}."}]
        plain = generate(msg, False, 1000 + i)
        wm = generate(msg, True, 1000 + i)
        para = generate([{"role": "user", "content": "Paraphrase the following paragraph in your own words. Keep the meaning, change the wording and sentence structure. Output only the paraphrase.\n\n" + wm}], False, 2000 + i)
        ed = edit(wm, pool, 0.30, rng)
        fr = generate([{"role": "user", "content": "Translate the following paragraph into French. Output only the translation.\n\n" + wm}], False, 3000 + i)
        rt = generate([{"role": "user", "content": "Translate the following paragraph into English. Output only the translation.\n\n" + fr}], False, 4000 + i)
        row = {"i": i, "topic": topic, "texts": {"human": human[i], "plain": plain, "watermarked": wm, "paraphrased": para, "edited30": ed, "translated_roundtrip": rt}, "french_intermediate": fr}
        row["detect"] = {k: detect(v) for k, v in row["texts"].items()}
        row["prefix_z"] = {c: {L: prefix_z(row["texts"][c], L) for L in (10, 25, 50, 100)} for c in ("watermarked", "plain", "human")}
        rows.append(row)
        print(i, topic, {k: round(v["z"], 2) for k, v in row["detect"].items()}, round(time.time() - t0), "s", flush=True)
        (D / "raw_runs.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    conds = ["human", "plain", "watermarked", "paraphrased", "edited30", "translated_roundtrip"]
    import statistics as st
    summ = {}
    for c in conds:
        zs = [r["detect"][c]["z"] for r in rows]; tk = [r["detect"][c]["tokens"] for r in rows]
        summ[c] = {"n": len(zs), "mean_z": st.mean(zs), "median_z": st.median(zs), "min_z": min(zs), "max_z": max(zs),
                   "flag_rate": sum(r["detect"][c]["flag"] for r in rows) / len(rows), "mean_green_frac": st.mean(r["detect"][c]["green_frac"] for r in rows), "mean_tokens": st.mean(tk), "z": zs}
    res = {"model": MODEL, "device": dev, "gamma": GAMMA, "delta": DELTA, "temperature": TEMP, "max_new_tokens": NEW_TOKENS,
           "z_threshold": Z_THRESHOLD, "n_prompts": N, "seeding": "keyed integer hash of (secret key, previous token id, candidate id) < gamma (context width 1)",
           "paraphraser": MODEL + " (same model, no watermark)", "translation_attack": "EN->FR->EN with the same model, no watermark", "edit_attack": "30% of words replaced by random words from human pool",
           "human_source": "wikitext-2-raw-v1 test split, first 150 words of 40 random long paragraphs", "conditions": summ,
           "runtime_s": time.time() - t0, "run_date": time.strftime("%Y-%m-%d %H:%M %Z"), "torch": torch.__version__}
    (D / "results.json").write_text(json.dumps(res, indent=1)); print(json.dumps({c: {k: v for k, v in s.items() if k != "z"} for c, s in summ.items()}, indent=1))
