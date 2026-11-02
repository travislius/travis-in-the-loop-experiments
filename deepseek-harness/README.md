# DeepSeek Harness: same model, three modes

**Video:** DeepSeek Harness Explained (Travis in the Loop)

Run on 2026-11-01. One model (`deepseek-v4-flash`, default reasoning), one harness (DeepSeek Harness **0.2.1rc2** via the Python SDK `deepseek-harness-sdk`), three shipped compositions:

- **Minimal** (`sdk-minimal` profile): one-sentence system prompt, `bash` + `read_image` + `working_directory`. DeepSeek's own test calls this "the exact RL prompt".
- **Standard** (`sdk` profile): 25 native tools.
- **PTC** (`sdk` profile + `patches/ptc.yml`, `tools.mode: ptc`): the model sees one tool, `run_code`, and writes TypeScript that calls the other tools.

These are small illustrative tasks with one model, **not a benchmark**.

## Setup
- Fresh copy of the task per run; DSH's own Seatbelt sandbox in `workspace-write` mode for every mode (`patches/confine*.yml`). `escape_probe.py` verified a write to `~/Desktop` is blocked in all three modes.
- Session-log upload to DeepSeek disabled (`patches/no-log-upload.yml`; the shipped default is enabled).
- Approvals off (no human in the loop); 15-minute cap per run; `max_tokens` 32768.
- Agents' `python3`: easy tasks inherited the host PATH (Python 3.14); hard tasks use `agent-bin/python3` → Python 3.11 (see rejected runs).
- Metrics are read from each run's own append-only session log (`analyze.py`). PTC "tool calls" counts `tools.*(` calls inside `run_code` programs.
- The original local runner read a key from macOS Keychain. This public runner requires `DEEPSEEK_API_KEY` in the environment. No keys are included.
- Published logs have only local paths/usernames redacted. Task inputs are synthetic fixtures, not real customer data.
- `analyze.py` writes `recomputed-results.json` and refuses absent/ambiguous logs. Success requires both a correct output and `finish_reason=completed`; a correct partial workspace at timeout does not count as completion.
- PTC inner-tool figures are counts of `tools.*(` call sites in the generated programs, not a dynamic execution trace; loops/retries can differ. This is the method used for the displayed comparison.

## Tasks (`tasks/`)
| id | what | graded by | runs/mode |
|---|---|---|---|
| bugfix | 4 planted bugs in a small invoice package | 8 visible tests + 5 hidden checks, tests unchanged | 3 |
| batch | 80 order JSON files (4 malformed, 2 refunds) → summary.json | exact totals + malformed list | 3 |
| calc | implement an expression evaluator from SPEC.md | 30 hidden checks, no eval/exec/ast | 5 |
| logs | 240 log files, 2 formats, 6 services → incident.json | 4 exact answers | 5 |

## What the model saw on its first request (median)
| mode | visible tools | first-request prompt tokens |
|---|---|---|
| Minimal | 3 | ~763 |
| Standard | 25 | ~6240 |
| PTC | 1 | ~7877 |

## Results (medians; 48 scored runs)
| task | mode | correct | wall s | model calls | tool calls | prompt tokens | output tokens | cache hit | shell hangs (300 s) |
|---|---|---|---|---|---|---|---|---|---|
| batch | minimal | 3/3 | 8.6 | 5 | 4 | 7,214 | 806 | 0.80 | 0 |
| batch | ptc | 3/3 | 12.7 | 6 | 8 | 52,675 | 1,468 | 0.96 | 0 |
| batch | standard | 3/3 | 10.2 | 5 | 5 | 34,470 | 1,177 | 0.95 | 0 |
| bugfix | minimal | 3/3 | 13.5 | 5 | 4 | 11,251 | 1,632 | 0.81 | 0 |
| bugfix | ptc | 3/3 | 32.6 | 7 | 9 | 81,221 | 5,151 | 0.95 | 0 |
| bugfix | standard | 3/3 | 22.5 | 5 | 11 | 46,129 | 4,065 | 0.93 | 0 |
| calc | minimal | 3/5 | 110.8 | 9 | 9 | 66,155 | 9,200 | 0.95 | 4 |
| calc | ptc | 5/5 | 127.2 | 13 | 16 | 317,673 | 21,738 | 0.97 | 0 |
| calc | standard | 5/5 | 131.1 | 12 | 16 | 221,925 | 18,707 | 0.97 | 0 |
| logs | minimal | 5/5 | 16.7 | 7 | 6 | 27,127 | 2,229 | 0.84 | 2 |
| logs | ptc | 5/5 | 33.9 | 10 | 8 | 134,999 | 4,846 | 0.94 | 0 |
| logs | standard | 5/5 | 34.9 | 12 | 15 | 193,203 | 5,023 | 0.94 | 0 |

- 46/48 runs correct. Standard and PTC 32/32. Both misses are Minimal on `calc`, where the persistent shell hung (300 s timeout, twice per run) and the run hit the 15-minute cap.
- Minimal used roughly 3–7× fewer prompt tokens than Standard/PTC on every task.
- PTC packed several tool calls per program but did not save tokens here; its generated TypeScript tool SDK is ~27k characters of system prompt.

Total API cost for all runs, including rejected ones: about $0.32.

## Rejected runs (`rejected/`, each with REASON.txt)
1. `bugfix-minimal-r0-nested-seatbelt-pty-fail` — I wrapped runs in my own `sandbox-exec`; macOS Seatbelt profiles don't nest, so DSH's PTY/bash failed to start.
2. `ptc-patch-silently-ignored` — my first PTC patch used row ids from the repo head that don't exist in 0.2.1rc2; dsh printed "entry not found" and ran Standard. `run_one.py` now aborts on any unapplied patch and checks `run_code` is visible in PTC.
3. `hard-v1-env-defects` — host `python3` was 3.9, which can't import the SPEC's `int | float` hints; fixed with `agent-bin/`.

## Rerun
```
python3.12 -m venv .venv && .venv/bin/pip install deepseek-harness-sdk==0.2.1rc2
mkdir -p agent-bin && ln -s $(which python3.11) agent-bin/python3
export DEEPSEEK_API_KEY=...
# Offline: recompute the published statistics without API calls:
python3 analyze.py
# A new paid run (choose an unused repetition number; existing evidence is protected):
./run.sh calc minimal 6
```
