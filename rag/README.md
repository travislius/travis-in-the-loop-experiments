# RAG on a manual for a product that doesn't exist

**Video:** RAG Explained: Why AI Answers Better When It Reads First

Run on 2026-10-25 with the OpenAI API.

## Idea
`corpus/bramble-b4-manual.md` is an owner's manual for the **Bramble B4**, a robot lawn mower that I invented for this test. No model can have seen it in training, so a correct answer requires reading it.

## Setup
- Chunking: one chunk per numbered section (15 chunks), each prefixed with `Bramble B4 manual, section N: <title>`.
- Embeddings: `text-embedding-3-small` (1,536 dimensions); retrieval by cosine similarity.
- Generator: `gpt-4.1-mini`, temperature 0.7. The system prompt asks for one or two sentences and the exact reply "I don't know." when the answer isn't known or isn't in the documents.
- 12 questions (`questions.json`): 10 have answers in the manual, 2 don't (camera resolution, top speed).
- Three conditions:
  - **closed**: just the question, no documents.
  - **rag**: the question plus the top 2 retrieved chunks.
  - **miss**: the question plus the 2 best chunks *after removing the correct section*, to simulate a retrieval miss (answerable questions only).
- 3 trials of everything → 102 answers.
- Grading (automatic, in `rag_demo.py`): "correct" if the answer contains every required fact string in `questions.json`; "abstain" if it says "I don't know"; otherwise "wrong". For the unanswerable questions any non-abstaining answer counts as wrong.

## Results
| Condition | Correct | Wrong | "I don't know" |
|---|---|---|---|
| Closed book, answerable (n=30) | 6 | 21 | 3 |
| Closed book, unanswerable (n=6) | – | 6 | 0 |
| RAG, answerable (n=30) | 30 | 0 | 0 |
| RAG, unanswerable (n=6) | – | 0 | 6 |
| Retrieval miss, answerable (n=30) | 0 | 0 | 30 |

- Closed-book correct answers were plausible guesses: default PIN 0000 (3/3), red blinks = blade jam (2/3), register for extra warranty (1/3).
- Retrieval put the correct section at rank 1 for 9 of 10 answerable questions. For "How much does Bramble Connect cost?" the correct section (13, anti-theft, cosine 0.440) ranked **2nd** behind section 15 (technical support, 0.453); it was only included because k=2.

Every request and response (with `x-request-id` and response `id`) is in `logs/requests.jsonl` (embedding vectors are summarised, not stored). `embedding-example.json` is one extra logged embeddings call used to show real vector values on screen.

## Run it
```
export OPENAI_API_KEY=...   # your own key
python rag_demo.py 3        # number of trials
```
Standard library only (Python 3.9+). Results will differ slightly between runs (temperature 0.7, model updates).

## Rejected runs
None. This is the only full run; no runs were discarded.

## Limits
Small, illustrative experiment: one fictional document, 12 questions, one model, a strict string-match grader, and an explicit instruction to abstain. It is not a benchmark.
