# AI Watermarks Explained — a minimal green-list text watermark, then attacks

Experiment for the Travis in the Loop video **AI Watermarks Explained**. A textbook implementation of the
Kirchenbauer et al. (2023) "soft" green-list watermark on a small open model, measured with the z-score test
before and after paraphrasing, random word swaps and translation round-trips.

**This is not SynthID-Text, not Anthropic's or OpenAI's production watermark.** It is a teaching-scale reproduction.

## Setup
- Model: `Qwen/Qwen2.5-1.5B-Instruct` (Hugging Face, fp16) on Apple silicon (`mps`), PyTorch 2.15.0
- Watermark: γ = 0.25 (green fraction), δ = 2.0 (logit bonus), context width 1 (previous token), secret key `15485863`
  - green list = keyed integer hash of (key, previous token id, candidate id) < γ (vectorized; see `green_mask`)
- Sampling: temperature 0.7, up to 200 new tokens, seeds 1000+i (generation), 2000+i (paraphrase), 3000+i / 4000+i (translation)
- Prompts: 40 topics, "Write one informative paragraph (about 150 words) explaining <topic>."
- Detection: re-tokenize text, count green hits over T tokens, z = (hits − γT)/√(Tγ(1−γ)); flag if z > 4.0
- Human baseline: first 150 words of random long paragraphs from wikitext-2-raw-v1 (test) — downloaded from Hugging Face, not committed
- Attacks: paraphrase by the same model (no watermark); 30% of whitespace words replaced by random words from the human pool; EN→FR→EN translation by the same model (no watermark)

## Results (n = 40 per row)

| Condition | mean z | median z | range | flagged (z>4) | green fraction | mean tokens |
|---|---|---|---|---|---|---|
| Human text (Wikipedia, wikitext-2) | 0.02 | -0.17 | -2.23 – 2.46 | 0/40 (0%) | 25.1% | 174 |
| Model output, no watermark | 0.37 | 0.09 | -1.41 – 3.29 | 0/40 (0%) | 26.3% | 157 |
| Model output, watermarked | 6.05 | 5.96 | 2.82 – 9.52 | 34/40 (85%) | 45.3% | 169 |
| Watermarked → paraphrased by same model | 2.76 | 2.64 | -1.18 – 6.92 | 11/40 (28%) | 34.5% | 156 |
| Watermarked → 30% of words randomly replaced | 3.16 | 3.51 | -0.56 – 7.29 | 8/40 (20%) | 35.5% | 174 |
| Watermarked → French → English (same model) | 2.11 | 2.15 | -1.11 – 5.17 | 6/40 (15%) | 33.0% | 127 |

### Length dependence — mean z on the first N tokens (flag rate)

| Text | 10 | 25 | 50 | 100 |
|---|---|---|---|---|
| human | -0.15 (0%) | -0.09 (0%) | -0.05 (0%) | -0.16 (0%) |
| plain | 0.27 (0%) | 0.27 (0%) | 0.27 (0%) | 0.35 (0%) |
| watermarked | 1.19 (2%) | 2.21 (5%) | 3.22 (20%) | 4.51 (57%) |

## Limitations
- One small model (1.5B), one key, one γ/δ setting, 40 prompts of ~150 words. Not a robustness benchmark.
- The paraphraser and translator are the same small model; a stronger model or a human rewrite would likely remove more of the signal.
- 0/40 human texts flagged cannot establish the theoretical ~3×10⁻⁵ false-positive rate at z > 4; that needs thousands of human texts.
- Wikipedia paragraphs are a convenient human baseline, not student essays.
- Total compute: ~73 min wall-clock on a Mac shared with other jobs. No API costs.

## Files
- `watermark.py` — generation + detection + attacks (writes `raw_runs.jsonl`, `results-run-raw.json` originally `results.json`)
- `analyze.py` — summary → `results.json`, and `sample-highlight.json` (token-level green/red of the median-z sample shown in the video)
- `write_units.py` — turns results into the narration numbers used in the video (no hand-typed numbers)
- `raw_runs.jsonl` — every text (all six versions) and its detection record
- `rejected/` — aborted first attempt (permutation-based green list was too slow, 2/40 prompts) + 2-prompt pilot, kept with reason

## Reproduce
```bash
uv venv .venv --python 3.12 && uv pip install --python .venv/bin/python torch transformers accelerate numpy pyarrow
# downloads Qwen/Qwen2.5-1.5B-Instruct and Salesforce/wikitext (wikitext-2-raw-v1) into the HF cache
.venv/bin/python -c "from huggingface_hub import snapshot_download as s; s('Qwen/Qwen2.5-1.5B-Instruct'); s('Salesforce/wikitext', repo_type='dataset', allow_patterns='wikitext-2-raw-v1/*')"
.venv/bin/python watermark.py 40
.venv/bin/python analyze.py 40
```

References: Kirchenbauer et al., *A Watermark for Large Language Models*, ICML 2023 (arXiv:2301.10226);
Dathathri et al., *Scalable watermarking for identifying large language model outputs*, Nature 634 (2024).
