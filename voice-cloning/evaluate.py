"""Score clones: ECAPA-TDNN speaker similarity (SpeechBrain spkrec-ecapa-voxceleb) vs held-out real Travis
(FormFactor video, never used as a prompt) + word error rate from Parakeet ASR. Baselines:
real-vs-real (leave-one-out over held-out clips) and a different speaker (Volcengine built-in 'Tim' narrator
clips from a previous episode, synthetic stock voice, not a real person's clone). Run with .venv-eval."""
from pathlib import Path
import json, re, glob, statistics as st, hashlib, platform
import numpy as np, torch, torchaudio, jiwer, speechbrain
from speechbrain.inference.speaker import EncoderClassifier

D = Path(__file__).resolve().parent
enc = EncoderClassifier.from_hparams(source='speechbrain/spkrec-ecapa-voxceleb', savedir=str(D / 'models/ecapa'))
def emb(path):
    x, sr = torchaudio.load(str(path)); x = x.mean(0, keepdim=True)
    if sr != 16000: x = torchaudio.functional.resample(x, sr, 16000)
    e = enc.encode_batch(x).squeeze().numpy(); return e / np.linalg.norm(e)
refs = json.loads((D / 'refs/REFS.json').read_text())
held = [emb(h['audio']) for h in refs['heldout']]
centroid = np.mean(held, 0); centroid /= np.linalg.norm(centroid)
def cos_to_centroid(e): return float(e @ centroid)
# real vs real: each held-out clip vs centroid of the others
loo = []
for i, e in enumerate(held):
    c = np.mean([h for j, h in enumerate(held) if j != i], 0); c /= np.linalg.norm(c); loo.append(float(e @ c))
# reference prompts themselves (different videos, same person)
refsim = {k: cos_to_centroid(emb(v['audio'])) for k, v in refs['conditions'].items()}
# other speaker baseline
TIM = sorted(glob.glob(str(D.parents[1] / '2026-10-24-Knowledge-Distillation-Explained/voice/processed/u*.wav')))[:12]
other = [cos_to_centroid(emb(p)) for p in TIM]
norm = lambda t: re.sub(r'[^a-z0-9 ]', ' ', t.lower().replace("'", '')).split()
rows = []
for j in sorted((D / 'clones').glob('*.json')):
    r = json.loads(j.read_text()); w = j.with_suffix('.wav'); a = json.loads((D / 'asr' / (w.stem + '.json')).read_text())
    rows.append({**{k: r[k] for k in ['condition', 'sentence', 'seed', 'ref_seconds', 'seconds']}, 'file': w.name,
                 'similarity': cos_to_centroid(emb(w)), 'asr': a['text'],
                 'wer': jiwer.wer(' '.join(norm(r['text'])), ' '.join(norm(a['text'])))})
summary = {}
for c in refs['conditions']:
    rs = [x for x in rows if x['condition'] == c]
    summary[c] = {'ref_seconds': rs[0]['ref_seconds'], 'n': len(rs), 'sim_mean': st.mean(x['similarity'] for x in rs), 'sim_sd': st.pstdev(x['similarity'] for x in rs),
                  'sim_min': min(x['similarity'] for x in rs), 'sim_max': max(x['similarity'] for x in rs), 'wer_mean': st.mean(x['wer'] for x in rs),
                  'perfect_transcripts': sum(x['wer'] == 0 for x in rs),
                  'per_seed_sim': {s: st.mean(x['similarity'] for x in rs if x['seed'] == s) for s in sorted({x['seed'] for x in rs})}}
for L in ['3', '10', '30']:
    rs = [x for x in rows if x['condition'] in (f'{L}s', f'{L}s_alt')]
    summary[f'{L}s_pooled'] = {'n': len(rs), 'sim_mean': st.mean(x['similarity'] for x in rs), 'wer_mean': st.mean(x['wer'] for x in rs),
                               'perfect_transcripts': sum(x['wer'] == 0 for x in rs)}
out = {'metric': 'cosine similarity of ECAPA-TDNN speaker embeddings to the centroid of held-out real Travis clips (higher = more alike)',
       'encoder': 'speechbrain/spkrec-ecapa-voxceleb', 'speechbrain': speechbrain.__version__, 'torch': torch.__version__, 'jiwer': jiwer.__version__ if hasattr(jiwer, '__version__') else '4.0.0',
       'heldout_clips': len(held), 'heldout_source': 'FormFactor video (not used in any prompt)',
       'baseline_real_vs_real_loo': {'mean': st.mean(loo), 'min': min(loo), 'max': max(loo), 'n': len(loo)},
       'baseline_other_speaker_tim': {'mean': st.mean(other), 'min': min(other), 'max': max(other), 'n': len(other)},
       'reference_prompt_similarity': refsim, 'summary': summary, 'rows': rows, 'platform': platform.platform()}
(D / 'results.json').write_text(json.dumps(out, indent=1))
print(json.dumps({k: out[k] for k in ['baseline_real_vs_real_loo', 'baseline_other_speaker_tim', 'reference_prompt_similarity', 'summary']}, indent=1))
