"""Needle-in-a-haystack / lost-in-the-middle probe for Long Context Explained.

Builds a synthetic, seeded logbook ("haystack") of a fictional harbor warehouse,
hides one target fact ("needle") at a chosen relative depth, and asks a real API
model to retrieve it. Two variants:
  plain       - haystack contains no other locker codes (classic NIAH)
  distractor  - haystack also contains many similar locker-code entries for
                OTHER colors, so the model must find the exact one.
Every request and full response (with response id) is appended to raw/requests.jsonl.

Key is read from env OPENAI_API_KEY. Stdlib only.
Usage: python needle_demo.py <run_name> [--models m1,m2] [--lengths 8000,32000,120000]
       [--depths 0,0.25,0.5,0.75,1] [--trials 3] [--variants plain,distractor]
"""
import json, os, random, sys, time, argparse, threading, urllib.request, hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

D = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument('run'); ap.add_argument('--models', default='gpt-4.1-mini,gpt-4.1-nano')
ap.add_argument('--lengths', default='8000,32000,120000'); ap.add_argument('--depths', default='0,0.25,0.5,0.75,1')
ap.add_argument('--trials', type=int, default=3); ap.add_argument('--variants', default='plain,distractor')
ap.add_argument('--workers', type=int, default=4)
ap.add_argument('--query-first', action='store_true', help='also state the question BEFORE the document (query-aware contextualization, Liu et al. 4.2)')
a = ap.parse_args()
OUT = D / 'raw' / a.run; OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / 'requests.jsonl'; lock = threading.Lock()
KEY = os.environ['OPENAI_API_KEY']

COLORS = ['red', 'green', 'amber', 'violet', 'white', 'black', 'orange', 'silver', 'pink', 'brown', 'gray', 'gold', 'teal', 'navy', 'olive', 'maroon']
NAMES = ['Ines', 'Tomas', 'Ruth', 'Felix', 'Mara', 'Oskar', 'Lena', 'Pavel', 'Greta', 'Hugo', 'Nadia', 'Arto', 'Celia', 'Bram', 'Wren', 'Dov']
GOODS = ['crates of tinned fish', 'coils of rope', 'barrels of lamp oil', 'sacks of flour', 'bolts of canvas', 'boxes of nails', 'drums of tar', 'bundles of timber', 'cases of glass jars', 'spools of copper wire']
WEATHER = ['A cold fog sat on the water all morning.', 'Light rain from the west, clearing by noon.', 'Strong wind; two moorings were checked twice.', 'Clear and calm; the tide came in late.', 'Sleet in the afternoon and the yard was slippery.']
EVENTS = ['{n} repaired a hinge on the north door.', '{n} counted {k} {g} and found the tally correct.', 'A barge unloaded {k} {g} before dusk.', '{n} swept the loft and moved the old ledgers to shelf {s}.', 'The night lamp was refilled by {n}.', '{n} reported a leak near bay {s}; it was patched with pitch.', 'Inspector {n} signed the weekly sheet without comment.', '{k} {g} were loaded for the river boat.']

def day_entry(rng, i, distractor_target):
    lines = [f'Day {i}.', rng.choice(WEATHER)]
    for _ in range(rng.randint(3, 5)):
        lines.append(rng.choice(EVENTS).format(n=rng.choice(NAMES), k=rng.randint(3, 90), g=rng.choice(GOODS), s=rng.randint(1, 40)))
    if distractor_target and rng.random() < 0.35:
        c = rng.choice([x for x in COLORS if x != distractor_target])
        lines.append(f'{rng.choice(NAMES)} noted that the combination for the {c} locker is {rng.randint(1000, 9999)}.')
    return ' '.join(lines)

def build(trial_seed, n_tokens, depth, variant):
    rng = random.Random(trial_seed)
    target = 'blue'; code = rng.randint(1000, 9999)
    needle = f'{rng.choice(NAMES)} noted that the combination for the {target} locker is {code}.'
    entries = []; chars = 0; i = 1
    budget = n_tokens * 4.1  # rough chars/token; real counts come from API usage
    while chars < budget:
        e = day_entry(rng, i, target if variant == 'distractor' else None); entries.append(e); chars += len(e) + 1; i += 1
    pos = round(depth * len(entries))
    # attach needle inside an entry so it reads naturally; depth 0 = first entry, 1 = last
    k = min(max(pos, 0), len(entries) - 1)
    entries[k] = entries[k] + ' ' + needle
    hay = '\n'.join(entries)
    return hay, code, needle, k, len(entries)

SYSTEM = 'You answer questions about the document the user provides. Answer with only the 4-digit number, nothing else. If it is not in the document, answer NONE.'
def ask(model, hay):
    # gpt-5.x: reasoning off (reasoning_effort=none) so this measures direct reading, not search-by-thinking
    extra = {'reasoning_effort': 'none', 'max_completion_tokens': 16} if model.startswith('gpt-5') else {'temperature': 0, 'max_tokens': 16}
    body = {'model': model, **extra, 'messages': [
        {'role': 'system', 'content': SYSTEM},
        {'role': 'user', 'content': ('Question: What is the combination for the blue locker?\n\n' if a.query_first else '') + 'DOCUMENT (warehouse logbook):\n<<<\n' + hay + '\n>>>\n\nQuestion: What is the combination for the blue locker?'}]}
    for attempt in range(6):
        req = urllib.request.Request('https://api.openai.com/v1/chat/completions', data=json.dumps(body).encode(), headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.loads(r.read()), time.time() - t0, r.headers.get('x-request-id')
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:500]
            with lock, (OUT / 'errors.jsonl').open('a') as f: f.write(json.dumps({'model': model, 'status': e.code, 'error': err, 'attempt': attempt, 't': time.time()}) + '\n')
            if e.code in (429, 500, 502, 503): time.sleep(5 * (attempt + 1)); continue
            raise
    raise RuntimeError('retries exhausted')

done = set()
if LOG.exists():
    for l in LOG.read_text().splitlines():
        r = json.loads(l); done.add(r['key'])
jobs = []
for model in a.models.split(','):
    for L in map(int, a.lengths.split(',')):
        for dp in map(float, a.depths.split(',')):
            for v in a.variants.split(','):
                for t in range(a.trials):
                    key = f'{model}|{L}|{dp}|{v}|{t}'
                    if key not in done: jobs.append((key, model, L, dp, v, t))
print('jobs', len(jobs), 'already', len(done), flush=True)
def work(j):
    key, model, L, dp, v, t = j
    seed = int(hashlib.sha256(f'{L}|{dp}|{v}|{t}'.encode()).hexdigest()[:8], 16)  # same haystack across models
    hay, code, needle, k, n = build(seed, L, dp, v)
    resp, dt, rid = ask(model, hay)
    ans = resp['choices'][0]['message']['content'].strip()
    rec = {'key': key, 'model': model, 'target_tokens': L, 'depth': dp, 'variant': v, 'trial': t, 'seed': seed,
           'needle': needle, 'expected': str(code), 'needle_entry': k, 'entries': n, 'haystack_sha256': hashlib.sha256(hay.encode()).hexdigest(),
           'answer': ans, 'correct': str(code) in ans, 'response_id': resp.get('id'), 'x_request_id': rid, 'model_returned': resp.get('model'),
           'usage': resp.get('usage'), 'latency_s': round(dt, 2), 'finish_reason': resp['choices'][0].get('finish_reason'), 'ts': time.time()}
    with lock, LOG.open('a') as f: f.write(json.dumps(rec) + '\n')
    print(('OK ' if rec['correct'] else 'MISS'), key, ans, rec['usage']['prompt_tokens'], flush=True)
with ThreadPoolExecutor(a.workers) as ex: list(ex.map(work, jobs))
(OUT / 'CONFIG.json').write_text(json.dumps({**vars(a), 'system': SYSTEM, 'temperature': 0, 'max_tokens': 16}, indent=1))
print('DONE')
