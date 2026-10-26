"""RAG experiment for 'RAG Explained' (Travis in the Loop, 2026-10-25).

Fictional manual (corpus/bramble-b4-manual.md) -> section chunks -> OpenAI embeddings ->
cosine top-k retrieval -> answer with gpt-4.1-mini under three conditions:
  closed   : question only (no documents)
  rag      : question + top-2 retrieved chunks
  miss     : question + 2 chunks that deliberately EXCLUDE the gold section
             (simulates a retrieval miss: the next-best chunks)
Every API request/response is logged with its request ID in logs/.
Key read from env OPENAI_API_KEY. Usage: python rag_demo.py [trials]
"""
import os, re, json, sys, time, hashlib, math, pathlib, urllib.request

D = pathlib.Path(__file__).resolve().parent
LOG = D / 'logs'; LOG.mkdir(exist_ok=True)
KEY = os.environ['OPENAI_API_KEY']
EMB_MODEL = 'text-embedding-3-small'
CHAT_MODEL = 'gpt-4.1-mini'
TRIALS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
TOPK = 2
call_n = 0

def api(path, body):
    global call_n
    req = urllib.request.Request('https://api.openai.com/v1/' + path, data=json.dumps(body).encode(),
                                 headers={'Authorization': 'Bearer ' + KEY, 'Content-Type': 'application/json'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                out = json.loads(r.read()); rid = r.headers.get('x-request-id'); break
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 4: time.sleep(2 ** attempt); continue
            raise
    call_n += 1
    rec = {'n': call_n, 'endpoint': path, 'x_request_id': rid, 'response_id': out.get('id'), 'time': time.time(),
           'request': body if path != 'embeddings' else {**body, 'input': body['input'] if isinstance(body['input'], str) else f"<{len(body['input'])} texts>"},
           'response': out if path != 'embeddings' else {'model': out['model'], 'usage': out['usage'], 'dims': len(out['data'][0]['embedding']), 'count': len(out['data'])}}
    with open(LOG / 'requests.jsonl', 'a') as f: f.write(json.dumps(rec) + '\n')
    return out

# ---------- chunking: one chunk per numbered section ----------
text = (D / 'corpus/bramble-b4-manual.md').read_text()
chunks = []
for m in re.finditer(r'^## (\d+)\. (.+?)\n(.*?)(?=^## |\Z)', text, re.S | re.M):
    chunks.append({'id': int(m.group(1)), 'title': m.group(2).strip(), 'text': f"Bramble B4 manual, section {m.group(1)}: {m.group(2).strip()}\n{m.group(3).strip()}"})
assert len(chunks) == 15

def embed(texts):
    out = api('embeddings', {'model': EMB_MODEL, 'input': texts})
    return [d['embedding'] for d in out['data']]
def cos(a, b):
    return sum(x * y for x, y in zip(a, b)) / math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))

QS = json.loads((D / 'questions.json').read_text())
cvec = embed([c['text'] for c in chunks])
qvec = embed([q['q'] for q in QS])

SYS = ("You are a helpful assistant answering questions about the Bramble B4 robot lawn mower. "
       "Answer in one or two sentences. If you do not know the answer, or the provided documents do not contain it, "
       "reply exactly: I don't know.")
def prompt(q, ctx):
    if ctx is None: return q['q']
    docs = '\n\n'.join(f"[Doc {i+1}] {c['text']}" for i, c in enumerate(ctx))
    return f"Use only these documents to answer.\n\n{docs}\n\nQuestion: {q['q']}"

def grade(q, ans):
    a = ans.lower()
    if "i don't know" in a or "i don’t know" in a: return 'abstain'
    if q.get('gold_section') is None: return 'wrong'  # unanswerable: any answer is a fabrication
    ok = all(any(alt.lower() in a for alt in group) for group in q['must'])
    return 'correct' if ok else 'wrong'

retrieval = []
for q, qv in zip(QS, qvec):
    sims = sorted(((cos(qv, cv), c['id']) for c, cv in zip(chunks, cvec)), reverse=True)
    retrieval.append({'qid': q['id'], 'ranking': [{'section': s, 'sim': round(v, 4)} for v, s in sims],
                      'gold': q.get('gold_section'), 'gold_rank': next((i + 1 for i, (_, s) in enumerate(sims) if s == q.get('gold_section')), None)})

rows = []
for t in range(TRIALS):
    for q, r in zip(QS, retrieval):
        byid = {c['id']: c for c in chunks}
        top = [byid[x['section']] for x in r['ranking'][:TOPK]]
        miss = [byid[x['section']] for x in r['ranking'] if x['section'] != q.get('gold_section')][:TOPK]
        for cond, ctx in [('closed', None), ('rag', top), ('miss', miss)]:
            if cond == 'miss' and q.get('gold_section') is None: continue
            body = {'model': CHAT_MODEL, 'temperature': 0.7, 'messages': [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': prompt(q, ctx)}]}
            out = api('chat/completions', body)
            ans = out['choices'][0]['message']['content'].strip()
            rows.append({'trial': t + 1, 'qid': q['id'], 'condition': cond, 'context_sections': [c['id'] for c in ctx] if ctx else [],
                         'answer': ans, 'grade': grade(q, ans), 'response_id': out['id'], 'log_n': call_n})
            print(t + 1, q['id'], cond, rows[-1]['grade'], '|', ans[:90], flush=True)

summary = {}
for cond in ['closed', 'rag', 'miss']:
    for kind in ['answerable', 'unanswerable']:
        rs = [x for x in rows if x['condition'] == cond and ((next(q for q in QS if q['id'] == x['qid']).get('gold_section') is None) == (kind == 'unanswerable'))]
        if rs: summary[f'{cond}/{kind}'] = {g: sum(x['grade'] == g for x in rs) for g in ['correct', 'wrong', 'abstain']} | {'n': len(rs)}
res = {'date': time.strftime('%Y-%m-%d %H:%M:%S %Z'), 'embedding_model': EMB_MODEL, 'chat_model': CHAT_MODEL, 'temperature': 0.7, 'top_k': TOPK,
       'trials': TRIALS, 'chunks': [{'id': c['id'], 'title': c['title'], 'chars': len(c['text'])} for c in chunks],
       'corpus_sha256': hashlib.sha256(text.encode()).hexdigest(), 'retrieval': retrieval, 'summary': summary, 'rows': rows, 'api_calls': call_n}
(D / 'results.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps(summary, indent=1)); print('retrieval gold ranks', [(r['qid'], r['gold_rank']) for r in retrieval])
