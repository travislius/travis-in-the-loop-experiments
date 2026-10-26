"""Transcribe every clone with Parakeet TDT 0.6B v3 (MLX) -> asr/<name>.json. Run with the parakeet venv."""
from pathlib import Path
import os, json, hashlib
os.environ['HF_HUB_OFFLINE'] = '1'
from parakeet_mlx import from_pretrained
D = Path(__file__).resolve().parent; A = D / 'asr'; A.mkdir(exist_ok=True)
root = Path.home() / '.cache/huggingface/hub/models--mlx-community--parakeet-tdt-0.6b-v3/snapshots'
snap = next(root.iterdir()); m = from_pretrained(str(snap))
for w in sorted((D / 'clones').glob('*.wav')):
    o = A / (w.stem + '.json')
    if o.exists(): continue
    r = m.transcribe(str(w))
    o.write_text(json.dumps({'audio_sha256': hashlib.sha256(w.read_bytes()).hexdigest(), 'text': r.text, 'asr': 'parakeet-tdt-0.6b-v3', 'snapshot': snap.name}))
print('ASR done', len(list(A.glob('*.json'))))
