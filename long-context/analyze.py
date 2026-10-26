"""Aggregate raw/<run>/requests.jsonl into results.json (accuracy per model/variant/length/depth)."""
import json, sys, collections
from pathlib import Path
D = Path(__file__).resolve().parent
run = sys.argv[1] if len(sys.argv) > 1 else 'main'
R = [json.loads(l) for l in (D / 'raw' / run / 'requests.jsonl').read_text().splitlines()]
assert len(R) == len({r['key'] for r in R})
g = collections.defaultdict(list)
for r in R: g[(r['model'], r['variant'], r['target_tokens'], r['depth'])].append(r['correct'])
models = sorted({r['model'] for r in R}); variants = ['plain', 'distractor']
lengths = sorted({r['target_tokens'] for r in R}); depths = sorted({r['depth'] for r in R})
grid = {m: {v: {str(L): {str(d): [sum(g[(m, v, L, d)]), len(g[(m, v, L, d)])] for d in depths} for L in lengths} for v in variants} for m in models}
mean_prompt = {str(L): round(sum(r['usage']['prompt_tokens'] for r in R if r['target_tokens'] == L) / sum(1 for r in R if r['target_tokens'] == L)) for L in lengths}
wrong = collections.Counter(r['answer'] for r in R if not r['correct'])
out = {'run': run, 'requests': len(R), 'models_returned': sorted({r['model_returned'] for r in R}), 'grid_correct_of_trials': grid,
       'mean_prompt_tokens': mean_prompt, 'wrong_answers': dict(wrong),
       'totals': {f'{m}|{v}': [sum(r['correct'] for r in R if r['model'] == m and r['variant'] == v), sum(1 for r in R if r['model'] == m and r['variant'] == v)] for m in models for v in variants}}
(D / 'results.json').write_text(json.dumps(out, indent=1)); print(json.dumps(out['totals']), out['wrong_answers'])
