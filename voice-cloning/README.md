# Voice cloning: how much of my own voice does a clone need?

**Video:** Voice Cloning Explained (Travis in the Loop)

Run on 2026-10-25, fully local on an Apple Silicon Mac. **Only the channel owner's own voice was cloned**, from his own recordings, with his permission. Nothing was uploaded to any service.

## Setup
- **Cloning model:** Qwen3-TTS-12Hz-1.7B-Base, bf16 MLX conversion (`mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16`, snapshot `a6eb4f68e4b056f1215157bb696209bc82a6db48`), via `mlx-audio` 0.5.8 / `mlx` 0.32.3. In-context cloning: reference audio + its transcript. temperature 0.9, top_k 50, top_p 1.0, repetition_penalty 1.5. Native output, no edits.
- **Prompts (2 independent sets × 3 lengths):** set A from a Mac review video, set B from a laptop review video. ~3 s (single clip cut at a word boundary, mid-sentence), ~11 s (one clip), ~35 s (4–5 clips joined with 0.3 s gaps). See `REFS.json`.
- **Texts:** 4 new sentences (in `generate_clones.py`), never spoken by Travis. **Seeds:** 11, 22, 33. → 6 prompts × 4 sentences × 3 seeds = **72 clips**.
- **Held-out real voice:** 26 clips from a third video (foldable phones), never used as a prompt.
- **Speaker similarity:** SpeechBrain ECAPA-TDNN (`speechbrain/spkrec-ecapa-voxceleb`, speechbrain 1.0.3, torch 2.8.0). Score = cosine similarity between the clip embedding and the normalized mean embedding of the 26 held-out clips.
- **Rulers:** real-vs-real = each held-out clip vs. the mean of the other 25 (leave-one-out). Different voice = 12 narration clips from a stock built-in TTS voice (Volcengine “Tim”), not a real person's clone.
- **Words:** Parakeet TDT 0.6B v3 (MLX) transcribes each clone; WER via `jiwer` after lowercasing/stripping punctuation.

## Results
Rulers: real-vs-real **0.904** (min 0.840, max 0.944, n=26); different voice **0.351** (n=12).

| Prompt length | Similarity (mean) | WER | Perfect transcripts |
|---|---|---|---|
| 3s | 0.757 | 1.4% | 20/24 |
| 10s | 0.779 | 0.4% | 23/24 |
| 30s | 0.808 | 0.0% | 24/24 |

Per prompt set (12 clips each):

| Condition | Prompt | Similarity mean ± sd | Range | WER | Perfect |
|---|---|---|---|---|---|
| 3s | 3.3 s | 0.793 ± 0.026 | 0.726–0.832 | 2.9% | 8/12 |
| 3s_alt | 3.2 s | 0.720 ± 0.032 | 0.664–0.767 | 0.0% | 12/12 |
| 10s | 11.4 s | 0.781 ± 0.025 | 0.726–0.814 | 0.8% | 11/12 |
| 10s_alt | 11.5 s | 0.777 ± 0.039 | 0.701–0.829 | 0.0% | 12/12 |
| 30s | 36.2 s | 0.804 ± 0.022 | 0.767–0.840 | 0.0% | 12/12 |
| 30s_alt | 34.6 s | 0.812 ± 0.031 | 0.760–0.855 | 0.0% | 12/12 |

- More reference audio helps, modestly. No clone reached the real-vs-real ruler on average; the best single clone scored 0.855, above the lowest real-vs-real clip (0.840).
- With 3 s, the choice of clip mattered (set A 0.79 vs. set B 0.72).
- All WER > 0 cases are a stray leading/trailing word: 4 of 12 set-A 3 s clips began with a word that continues the prompt (“six”, “politics” — the 3 s prompt ends “…projects, M6”), and one 10 s clip ended with an extra “and”.

## Files
- `prepare_refs.py` — builds prompts and the held-out list (needs the private source clips; path via `TRAVIS_CORPUS`).
- `generate_clones.py` — runs the 72 generations (MLX-Audio venv). `clone-receipts/` = per-clip parameters, durations and SHA-256.
- `asr_clones.py`, `asr/` — transcripts. `evaluate.py` → `results.json` (every row). `embed_pca.py` → `pca.json` (2-D map shown in the video).
- `requirements-eval.txt` — evaluation environment.

## What is NOT included, and why
- **No audio.** Travis's source recordings and the 72 synthetic clips of his voice are not published, to avoid giving anyone ready-made material to impersonate him. Hashes are listed so results are verifiable against the private files. To reproduce, use **your own** voice (or one you have explicit consent for).
- No rejected runs: all 72 planned generations completed; none were discarded.

## Limits
One speaker, one model, 4 sentences, cosine similarity from one verification model. ASR-based WER does not measure naturalness or prosody. Not a benchmark.

## Ethics
Clone only your own voice or a voice you have clear permission to use, and disclose synthetic audio. See the FTC's guidance on voice-cloning scams: https://consumer.ftc.gov/consumer-alerts/2023/03/scammers-use-ai-enhance-their-family-emergency-schemes
