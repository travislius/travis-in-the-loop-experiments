# AI hallucination: checkable source vs. nonexistent paper

**Video:** AI Hallucination Explained: Why Fluent Answers Aren't Always True

Run on 2026-10-24 via the OpenAI Chat Completions API.

- Models: `gpt-4o-mini-2024-07-18` (temperature 1.0, max_tokens 200), `gpt-5-mini-2025-08-07` (provider defaults).
- Open-book: a short fictional community-garden memo; 4 questions (answer in memo / not in memo ×2 / nonexistent "section 7"); 3 prompt styles (just answer, answer only from memo, quote supporting line first); 3 trials each.
- Closed-book: summarize a fictional paper, "Recursive Lantern Networks for Sparse Memory" (Okafor & Lindqvist, NeurIPS 2019). The paper, authors and memo were invented for the test. 2 prompt styles × 3 trials.
- Total: 84 responses.

## Files
- `run_demo.py` — the script (set `OPENAI_API_KEY` in your environment; refuses to overwrite an existing `runs.jsonl`).
- `runs.jsonl` — every request and response, with response IDs.
- `DEMO-CONFIG.json` — memo, questions, prompts, timing.
- `TALLY.json` — keyword-based tally; every response was also read manually.

## Results
- With the memo: 0 of 72 answers claimed the memo said something it didn't.
- Fake paper, "just answer": gpt-4o-mini summarized it 3/3; gpt-5-mini said it couldn't find a record 3/3.
- Adding one "say if you can't verify" sentence: gpt-4o-mini declined to invent 3/3.

Small test, two models, one day. Not a benchmark.
