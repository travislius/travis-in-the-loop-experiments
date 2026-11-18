# Local AI on a laptop: Flint 40B-A2.5B MoE vs. a dense 32B model (llama.cpp, M5 Max)

**Video:** Local AI Explained: How a 40B Model Runs on a Laptop

Run on 2026-11-17 on an Apple M5 Max (40-core GPU, 64 GB unified memory; Apple spec: up to 614 GB/s), macOS 27.2.1, llama.cpp built from source at commit `52975342ff6b85127ff31930d39e36725fd08809 Wed Nov 18 00:12:20 2026 +0100` (Metal, flash attention on, all layers offloaded).

## Setup
- Models (GGUF, **not in this repo** — download from Hugging Face; SHA-256 verified against the HF LFS ids, see `SHA256-VERIFY.txt`):
  - `ggml-org/Flint-GGUF` → `Flint-Q4_K_M.gguf`, `Flint-Q8_0.gguf` (Recursive Flint, 39.8B total / ~2.5B active, Apache-2.0)
  - `Qwen/Qwen3-32B-GGUF` → `Qwen3-32B-Q4_K_M.gguf` (dense, all ~32.8B parameters active)
- Speed: `llama-bench -p 512 -n 128 -d 0,8192,32768 -r 3 -fa 1 -ngl 99`. `pp` = prompt processing (prefill) tokens/s, `tg` = generation (decode) tokens/s; `-d` = tokens already in the KV cache.
- Memory: one `llama-completion` run per model (`-c 8192`, 200 tokens, greedy, `-v`); weights and KV-cache sizes as reported by llama.cpp; `/usr/bin/time -l` max RSS.
- Quality: `llama-perplexity` on WikiText-2 raw test, 60 chunks × 512 tokens (Flint Q4 vs. Q8 only; different tokenizers make cross-model perplexity meaningless).
- Bits per weight = file bits ÷ parameter count reported by llama.cpp.
- Each stage ran while holding the shared local-GPU lock used by our TTS jobs (`locked_run.py`), but **other video renders (ffmpeg, headless Chrome) were running on the same Mac**; `raw/bench-*.json` records the busy processes before/after each run.

## Results
| model | quant | file | bits/weight | weights loaded | KV cache @8K ctx | pp512 tok/s | tg128 tok/s | tg @8K | tg @32K | pp @32K | perplexity ↓ |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Flint 40B-A2.5B MoE | Q4_K_M | 23.39 GB | 4.70 | 23.4 GB | 312 MiB | 2030 ± 1092 | 51.8 ± 7.9 | 54.8 | 35.5 | 999 | 21.68 ± 0.70 |
| Qwen3-32B dense | Q4_K_M | 19.76 GB | 4.83 | 19.8 GB | 2048 MiB | 648 ± 5 | 21.7 ± 0.3 | 15.9 | 12.8 | 110 | — |
| Flint 40B-A2.5B MoE | Q8_0 | 42.35 GB | 8.52 | 42.3 GB | 312 MiB | 284 ± 119 | 11.1 ± 1.0 | 11.1 | 9.2 | 356 | 20.77 ± 0.66 |

Derived (estimates): Qwen3-32B reads ≈ 19.8 GB of weights per token → 21.7 tok/s × that ≈ 429 GB/s (≈70% of 614 GB/s). Flint (2.5B active × 4.70 bits) ≈ 1.47 GB per token → ≈ 76 GB/s: MoE routing overhead, far from the bandwidth ceiling.

Flint BF16 (`Flint-BF16.gguf`, 79.63 GB) was not run: it does not fit in 64 GB.

## Findings and caveats
- 4-bit Flint (MoE) generated ~2.4× faster than the dense 32B model at a similar weight footprint, and its 8K KV cache was ~6.6× smaller (sliding-window attention in 35 of 49 layers).
- **Flint Q8_0 (42.35 GB) was memory-starved on this machine:** max RSS during the memory run was 39.5 GB (< file size), loading took minutes, and decode ran ~11 tok/s. With other work using memory, macOS could not keep all weights resident. A separate paging-evidence run (`paging_check.py flint-q8`) did not finish in >16 minutes and was killed to release the shared GPU lock — see `rejected/`. The Q8 speed numbers therefore reflect paging, not bandwidth scaling.
- Speeds varied between runs because of concurrent renders (e.g. a later generation-only Q4 run measured 36.6 tok/s, `raw/paging-flint-q4.json`). Report ranges, not a ranking.
- Perplexity on Wikipedia is not coding ability; these are community GGUF quants, not Recursive's own QAT/NVFP4 release.

## Reproduce
```bash
git clone https://github.com/ggml-org/llama.cpp && cd llama.cpp && cmake -B build && cmake --build build -j --target llama-bench llama-completion llama-perplexity
export LLAMA_BIN=$PWD/build/bin
# put the three GGUF files in models/ and WikiText-2 raw in data/wikitext-2-raw/
python3 run_experiment.py env
python3 run_experiment.py bench flint-q4 qwen32-q4 flint-q8
python3 run_experiment.py memory flint-q4 qwen32-q4 flint-q8
python3 run_experiment.py ppl flint-q4 flint-q8
python3 analyze.py
```
No API keys or paid services are used.
