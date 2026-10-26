"""2-D PCA of ECAPA speaker embeddings: held-out real Travis, a different (stock synthetic) voice, and all 72 clones.
Run with .venv-eval after evaluate.py. Writes pca.json (for the on-screen 'voice fingerprint' map)."""
from pathlib import Path
import json, glob
import numpy as np, torchaudio
from speechbrain.inference.speaker import EncoderClassifier
D = Path(__file__).resolve().parent
enc = EncoderClassifier.from_hparams(source='speechbrain/spkrec-ecapa-voxceleb', savedir=str(D / 'models/ecapa'))
def emb(p):
    x, sr = torchaudio.load(str(p)); x = x.mean(0, keepdim=True)
    if sr != 16000: x = torchaudio.functional.resample(x, sr, 16000)
    e = enc.encode_batch(x).squeeze().numpy(); return e / np.linalg.norm(e)
refs = json.loads((D / 'refs/REFS.json').read_text())
pts = [('real', h['id'], emb(h['audio'])) for h in refs['heldout']]
pts += [('other', Path(p).stem, emb(p)) for p in sorted(glob.glob(str(D.parents[1] / '2026-10-24-Knowledge-Distillation-Explained/voice/processed/u*.wav')))[:12]]
for w in sorted((D / 'clones').glob('*.wav')): pts.append(('clone-' + w.stem.split('__')[0].replace('_alt', ''), w.stem, emb(w)))
X = np.stack([p[2] for p in pts]); mu = X.mean(0); U, S, Vt = np.linalg.svd(X - mu, full_matrices=False); Y = (X - mu) @ Vt[:2].T
ev = (S**2 / (S**2).sum())[:2]
(D / 'pca.json').write_text(json.dumps({'explained_variance_ratio': ev.tolist(), 'points': [{'group': g, 'id': i, 'x': float(y[0]), 'y': float(y[1])} for (g, i, _), y in zip(pts, Y)]}, indent=1))
print('pca', len(pts), ev)
