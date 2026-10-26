# Model quantization on a Mac (Qwen2.5-1.5B-Instruct, bf16 → 8/4/3/2-bit)

**Video:** Model Quantization Explained: Same Model, Fewer Bits

Run on 2026-10-25 on an Apple M5 Max (64 GB, macOS 27.0.1) with MLX 0.32.4 / mlx-lm 0.32.2, Python 3.12.12.
Exact environment: `requirements-lock.txt`.

## Setup
- Model: [`Qwen/Qwen2.5-1.5B-Instruct`](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct), snapshot `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`. **Weights are not in this repo** — `python quant_demo.py convert` downloads them from Hugging Face and writes `models/<variant>/`. SHA-256 of every produced `.safetensors` file is in `results/convert.json`.
- Variants: bf16 original, and `mlx_lm.convert` affine quantization at 8, 4, 3, 2 bits, group size 64 (plain round-to-nearest; no GPTQ/AWQ calibration).
- Size: total bytes of the `.safetensors` files.
- Speed: greedy generation of 256 new tokens from one fixed prompt (bf16 hit EOS at 248), after a warm-up; 3 repetitions × 3 separate runs = 9 timings per variant. Runs were serialized under an exclusive lock so no renders/benchmarks ran concurrently. Peak memory = MLX peak memory during generation.
- Perplexity: 40 non-overlapping 512-token windows from the start of the WikiText-2 (raw) test split (`Salesforce/wikitext`, file hash in `results/quality-*.json`), 20,440 scored tokens.
- QA: 20 fixed easy factual questions (in `quant_demo.py`), greedy, max 24 tokens; correct if the answer contains an expected string. Every answer is saved in `results/quality-*.json`.
- Hand rounding: first 64 weights of row 0 of `model.layers.0.self_attn.q_proj.weight` (bf16), quantized with `mx.quantize(bits=4, group_size=64)`; the hand formula `code = round((w - bias)/scale)` reproduces MLX's reconstruction exactly (max diff 0.0).

## Results
| variant | weights on disk | peak memory | tokens/s median (min–max) | vs bf16 | perplexity ↓ | QA |
|---|---|---|---|---|---|---|
| bf16 | 3.087 GB | 3.13 GB | 156.5 (154.8–157.5) | 1.00× | 11.96 | 20/20 |
| q8 | 1.640 GB | 1.79 GB | 258.4 (255.3–262.1) | 1.65× | 11.96 | 20/20 |
| q4 | 0.869 GB | 1.01 GB | 368.6 (365.7–370.8) | 2.35× | 13.67 | 19/20 |
| q3 | 0.676 GB | 0.81 GB | 393.9 (386.6–395.8) | 2.52× | 29.09 | 16/20 |
| q2 | 0.483 GB | 0.62 GB | 475.3 (471.2–479.2) | 3.04× | 31,850.82 | 0/20 |

Hand example (4-bit, group 64): mean |error| 0.00097 vs mean |weight| 0.0114.

## Caveats
One small model, one machine, one text slice, 20 easy questions. Not a benchmark. Larger models and better methods (GPTQ, AWQ) typically hold up better at low bit widths; harder tasks can degrade earlier.

## Superseded attempt (not kept)
The first version of the hand-rounding step used my own min/max formula, which differed from MLX's quantizer by up to 0.0035 per weight (MLX picks scale/bias differently). It was replaced by the MLX-matching version above before any number was used in the video.

## Reproduce
```
uv venv -p 3.12 .venv && uv pip install -p .venv/bin/python mlx-lm pyarrow
.venv/bin/python quant_demo.py convert
.venv/bin/python quant_demo.py rounding
.venv/bin/python quant_demo.py quality
for i in 1 2 3; do .venv/bin/python quant_demo.py speed run$i; done
.venv/bin/python summarize.py
```
