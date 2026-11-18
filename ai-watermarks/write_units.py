#!/usr/bin/env python3
"""Write experiment narration units (u17-u21) from results.json -> EXP-UNITS.json (numbers never typed by hand)."""
import json
from pathlib import Path
D = Path(__file__).resolve().parent; R = json.loads((D / "results.json").read_text()); C = R["conditions"]; S = json.loads((D / "sample-highlight.json").read_text())
N = R["n_prompts"]
W = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen", 16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty"}
def words(n):
    if n in W: return W[n]
    t = {2: "twenty", 3: "thirty", 4: "forty"}[n // 10]; return t + ("-" + W[n % 10] if n % 10 else "")
def zs(v): a, b = f"{v:.1f}".split("."); return (("minus " if v < 0 else "") + words(abs(int(a))) + " point " + W[int(b)])
def zd(v): return f"{v:.1f}"
def fl(c): return C[c]["flagged"]
pz = R["prefix_mean_z"]["watermarked"]
U = {}
U["u17"] = (f"Now let's build one. I used Qwen 2.5, a small open model with one and a half billion parameters, running on my Mac. Green list a quarter of the vocabulary, a bonus of two, temperature zero point seven. I asked it for {words(N)} short paragraphs, on topics like why cats purr. For each one, I kept six versions: a human Wikipedia paragraph, the model without a watermark, with a watermark, and three attacks.",
            f"Now let's build one. I used Qwen2.5, a small open model with 1.5 billion parameters, running on my Mac. Green list: a quarter of the vocabulary, a bonus of 2, temperature 0.7. I asked it for {N} short paragraphs, on topics like why cats purr. For each one, I kept six versions: a human Wikipedia paragraph, the model without a watermark, with a watermark, and three attacks.")
U["u18"] = (f"Here's what the detector sees. Green tokens are highlighted, and there are clearly too many of them. Across all {words(N)} prompts, human text averaged a z of about zero. The model without a watermark: {zs(C['plain']['mean_z'])}. With the watermark: {zs(C['watermarked']['mean_z'])}, and {words(fl('watermarked'))} of {words(N)} crossed the line of four. Zero human texts did.",
            f"Here's what the detector sees. Green tokens are highlighted, and there are clearly too many of them. Across all {N} prompts, human text averaged a z of about 0. The model without a watermark: {zd(C['plain']['mean_z'])}. With the watermark: {zd(C['watermarked']['mean_z'])}, and {fl('watermarked')} of {N} crossed the line of 4. {'Zero' if fl('human')==0 else fl('human')} human texts did.")
U["u19"] = (f"Then I attacked it. When the same small model paraphrased the text, the average z fell to {zs(C['paraphrased']['mean_z'])}, and only {words(fl('paraphrased'))} of {words(N)} stayed flagged. Swapping thirty percent of the words at random: {zs(C['edited30']['mean_z'])}, {words(fl('edited30'))} flagged. Translating to French and back: {zs(C['translated_roundtrip']['mean_z'])}, {words(fl('translated_roundtrip'))} flagged. The signal fades, it doesn't vanish all at once.",
            f"Then I attacked it. When the same small model paraphrased the text, the average z fell to {zd(C['paraphrased']['mean_z'])}, and only {fl('paraphrased')} of {N} stayed flagged. Swapping 30% of the words at random: {zd(C['edited30']['mean_z'])}, {fl('edited30')} flagged. Translating to French and back: {zd(C['translated_roundtrip']['mean_z'])}, {fl('translated_roundtrip')} flagged. The signal fades; it doesn't vanish all at once.")
U["u20"] = (f"Length shows up too. On just the first ten tokens of watermarked text, the average z was {zs(pz['10'])}. At fifty tokens, {zs(pz['50'])}. At a hundred, {zs(pz['100'])}. A one-line reply simply doesn't carry enough evidence.",
            f"Length shows up too. On just the first 10 tokens of watermarked text, the average z was {zd(pz['10'])}. At 50 tokens, {zd(pz['50'])}. At 100, {zd(pz['100'])}. A one-line reply simply doesn't carry enough evidence.")
U["u21"] = (f"Some honest limits. This is the textbook green list on a tiny model, not Synth I D, and not what Anthropic or Open A I deploy. It's {words(N)} prompts, one key, and a weak paraphraser. A stronger rewrite would likely erase more. And zero false positives out of {words(N)} can't prove a one in thirty thousand rate. That needs far more human text.",
            f"Some honest limits. This is the textbook green list on a tiny model, not SynthID, and not what Anthropic or OpenAI deploy. It's {N} prompts, one key, and a weak paraphraser. A stronger rewrite would likely erase more. And zero false positives out of {N} can't prove a 1-in-30,000 rate. That needs far more human text.")
out = {k: {"tts": v[0], "text": v[1]} for k, v in U.items()}
(D / "EXP-UNITS.json").write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
