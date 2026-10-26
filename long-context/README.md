# Long context: needle in a haystack, with and without look-alikes

**Video:** Long Context Explained: Why AI Misses One Sentence in a Whole Book

Run on 2026-10-25 against the OpenAI Chat Completions API. 325 logged requests in the final runs.

## Setup
- `needle_demo.py` generates a seeded, synthetic **warehouse logbook** (weather, repairs, cargo counts by recurring names) and hides one *needle* sentence, e.g. `Ines noted that the combination for the blue locker is 7799.`
- Needle depth: 0 (first entry), 0.25, 0.5, 0.75, 1 (last entry).
- Target lengths: ~4K, ~32K, ~120K tokens. Mean **measured** prompt tokens (API `usage`): 4,070 · 31,697 · 118,990.
- Two versions:
  - **plain**: the needle is the only locker combination in the logbook (classic needle-in-a-haystack).
  - **distractor**: ~35% of day entries also state a combination for a *different* colored locker. Look-alike count: 25 (4K), 149 (32K), 601 (119K). Exactly one blue locker.
- Models: `gpt-4o-mini` (temperature 0, max_tokens 16) and `gpt-5.4-nano` (`reasoning_effort: none`, max_completion_tokens 16). Returned model ids: `gpt-4o-mini-2024-07-18`, `gpt-5.4-nano-2026-03-17`.
- System prompt asks for only the 4-digit number, or `NONE` if absent. The question comes **after** the document. A trial is correct if the exact code appears in the answer.
- 5 trials (5 different seeded logbooks) per cell. The same logbook is used for both models in a cell.
- Follow-up (`raw/queryfirst`): `gpt-4o-mini`, ~119K, distractor version, the **same 25 logbooks**, with the question stated **both before and after** the document (query-aware contextualization, Liu et al. 2023 §4.2).

## Results (correct out of 5)
**plain** — both models, every length and depth: **150/150**.

**distractor**

| gpt-4o-mini | start | 25% | 50% | 75% | end |
|---|---|---|---|---|---|
| ~4K | 5 | 5 | 5 | 5 | 5 |
| ~32K | 4 | 2 | 2 | 1 | 5 |
| ~119K | 2 | 0 | 0 | 0 | 5 |

| gpt-5.4-nano | start | 25% | 50% | 75% | end |
|---|---|---|---|---|---|
| ~4K | 5 | 5 | 5 | 5 | 5 |
| ~32K | 5 | 4 | 5 | 5 | 5 |
| ~119K | 5 | 2 | 3 | 3 | 5 |

- All 37 misses answered `NONE` (never a wrong code).
- Query before + after (gpt-4o-mini, ~119K, distractor): **22/25** (5, 5, 4, 3, 5 by depth) vs **7/25** with the question only after.

Every request is in `raw/<run>/requests.jsonl` with the needle, expected code, answer, `response_id`, `x_request_id`, token usage, latency and a SHA-256 of the exact haystack. `results.json` is produced by `analyze.py main`.

## Rejected / excluded runs
- `rejected/pilot-deprecated-model/` — first pilot used `gpt-4.1-nano`, which the API rejected (HTTP 404, model deprecated). No responses; error log kept.
- `rejected/pilot2-calibration/` — 12-request calibration at ~120K (depths 0/0.5/1, one trial) used to check the setup worked before the main grid. Excluded because it was a pilot with 1 trial per cell, not because of its outcome (it showed the same pattern: both models missed only the distractor-middle cell).

## Limits
Small, illustrative experiment: one synthetic task, two small models, 5 trials per cell; not a benchmark. Results will change with model versions.

## Run
```bash
export OPENAI_API_KEY=...   # never commit keys
python needle_demo.py main --models gpt-5.4-nano,gpt-4o-mini --lengths 4000,32000,120000 --depths 0,0.25,0.5,0.75,1 --trials 5
python needle_demo.py queryfirst --query-first --models gpt-4o-mini --lengths 120000 --variants distractor --trials 5
python analyze.py main
```
Stdlib only (Python 3.9+). The full grid costs roughly 20M input tokens.

References: Liu et al., "Lost in the Middle: How Language Models Use Long Contexts," arXiv:2307.03172. Hsieh et al., "RULER: What's the Real Context Size of Your Long-Context Language Models?," arXiv:2404.06654.
