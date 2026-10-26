"""Build 3 s / 10 s / 30 s reference prompts from Travis's own authorized recordings (M6 + Surface videos)
and a held-out real set from a different video (FormFactor). Word-boundary cuts use Parakeet timestamps.
Run with the parakeet venv. Writes refs/*.wav (24 kHz mono) + refs/REFS.json."""
from pathlib import Path
import os, json, hashlib
os.environ['HF_HUB_OFFLINE'] = '1'
import numpy as np, soundfile as sf
from parakeet_mlx import from_pretrained

D = Path(__file__).resolve().parent
CORPUS = Path(os.environ.get('TRAVIS_CORPUS', './my-voice-corpus'))
R = D / 'refs'; R.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
rows = {json.loads(l)['id']: json.loads(l) for l in open(CORPUS / 'manifest.jsonl')}
root = Path.home() / '.cache/huggingface/hub/models--mlx-community--parakeet-tdt-0.6b-v3/snapshots'
asr = from_pretrained(str(next(root.iterdir())))

def words(path):
    r = asr.transcribe(str(path))
    return [(t.text, t.start, t.end) for s in r.sentences for t in s.tokens], r.text

def load(i):
    x, sr = sf.read(rows[i]['audio'], dtype='float32'); assert sr == 24000; return x

out = {'corpus': str(CORPUS), 'speaker': 'Travis Li (channel owner, own recordings, authorized)', 'conditions': {}, 'heldout': []}
# 3 s: first ~3 s of M6_034, cut at the last token end <= 3.2 s
for cond, src, limit in [('3s', 'M6_034', 3.2), ('3s_alt', 'Surface_030', 3.2)]:
    toks, _ = words(rows[src]['audio']); keep = [t for t in toks if t[2] <= limit]
    end = keep[-1][2] + 0.08; text = ''.join(t[0] for t in keep).strip().replace('U2', 'YouTube')  # ASR fix, checked vs caption
    x = load(src)[: int(end * 24000)]
    p = R / f'{cond}.wav'; sf.write(p, x, 24000, subtype='PCM_16')
    out['conditions'][cond] = {'audio': str(p), 'text': text, 'seconds': len(x) / 24000, 'sources': [src], 'sha256': sha(p)}
# 10 s: single ~10-11 s M6/Surface clip
for cond, src in [('10s', 'M6_v2_2151_2190'), ('10s_alt', 'Surface_v2_0154_0192')]:
    x = load(src); p = R / f'{cond}.wav'; sf.write(p, x, 24000, subtype='PCM_16')
    out['conditions'][cond] = {'audio': str(p), 'text': rows[src]['text'], 'seconds': len(x) / 24000, 'sources': [src], 'sha256': sha(p)}
# 30 s+: concatenate several clips with 0.3 s gaps
for cond, srcs in [('30s', ['M6_034', 'M6_v2_0899_0921', 'M6_v2_1043_1067', 'M6_v2_0270_0292', 'M6_045']),
                   ('30s_alt', ['Surface_v2_0078_0115', 'Surface_v2_1524_1557', 'Surface_033', 'Surface_030'])]:
    gap = np.zeros(int(.3 * 24000), np.float32); parts = []
    for s in srcs: parts += [load(s), gap]
    x = np.concatenate(parts[:-1]); p = R / f'{cond}.wav'; sf.write(p, x, 24000, subtype='PCM_16')
    out['conditions'][cond] = {'audio': str(p), 'text': ' '.join(rows[s]['text'] for s in srcs), 'seconds': len(x) / 24000, 'sources': srcs, 'sha256': sha(p)}
# held-out real Travis: FormFactor video, never used as a prompt
for i, r in rows.items():
    if i.startswith('FormFactor'):
        out['heldout'].append({'id': i, 'audio': r['audio'], 'text': r['text'], 'sha256': sha(r['audio'])})
(R / 'REFS.json').write_text(json.dumps(out, indent=1))
for k, v in out['conditions'].items(): print(k, round(v['seconds'], 2), v['text'][:80])
print('heldout', len(out['heldout']))
