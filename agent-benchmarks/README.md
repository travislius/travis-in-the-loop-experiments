# Agent Benchmarks Explained — mini benchmark

Experiment from the Travis in the Loop video **Agent Benchmarks Explained** (Nov 2026).

## Setup
- 11 Python bug-fix tasks in `tasks/<task>/`: 8 standard (slugify, overlap, lru, money, merge, bucket, roman, semver) and 3 hard (cron, expr, glob).
  Each task has a buggy `repo/`, an `ISSUE.md` the agent sees, and a `hidden_test.py` it never sees.
  Every buggy repo fails its hidden tests; every solution in `reference/` passes them.
- Harness: DeepSeek Harness SDK `deepseek-harness-sdk==0.2.1rc2`, default settings, same harness for both models (`run_one.py`, `run.sh`).
- Models: `deepseek-flash` and `deepseek-v4-pro`. Each model ran each task 5 times, for 110 runs. The hard tier was added after the standard tier saturated.
- Pass criterion: all hidden tests pass. Cost = usage logs × DeepSeek list prices (cache hit / miss / output; peak vs. off-peak by run timestamp; all runs were off-peak).

## Results (`results.json`, `python3 analyze.py`)
| model | tier | attempts | pass@1 | pass^5 | median time | median output tokens | cost/attempt |
|---|---|---|---|---|---|---|---|
| deepseek-flash | easy | 40 | 100% | 100% | 25.9 s | 1880 | $0.0018 |
| deepseek-v4-pro | easy | 40 | 100% | 100% | 48.0 s | 2196 | $0.0079 |
| deepseek-flash | hard | 15 | 100% | 100% | 76.9 s | 9214 | $0.0094 |
| deepseek-v4-pro | hard | 15 | 100% | 100% | 158.5 s | 12167 | $0.0386 |

Total API bill: **$1.11**.

Finding: both models solved every attempt, so the completion rate and pass^5 tie at 100%. Time, tokens and cost still separate them. On the standard tasks, Pro took about 1.9× as long and cost about 4.4× as much.

## Limitations
11 small tasks, one harness, 5 attempts per task and two models. This is a demonstration of the metrics, not a model ranking.

## Reproduce
```
python3 -m venv .venv && .venv/bin/pip install deepseek-harness-sdk==0.2.1rc2 deepseek-harness-runtime-bin==0.2.1rc2 pytest
export DEEPSEEK_API_KEY=...   # never committed
./run_matrix.sh && ./run_matrix_hard.sh && python3 analyze.py
```
`runs/<task>-<model>-r<rep>/` holds each run's `result.json` and `patch.diff`. Local paths are redacted as `<EXPERIMENT>`, `<PATH>` and `<HOME>`.
