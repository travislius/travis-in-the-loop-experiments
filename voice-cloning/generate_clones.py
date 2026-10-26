"""Clone Travis's own voice (authorized) from 3 s / 10 s / 30 s references with local Qwen3-TTS 1.7B Base (MLX).
Same 4 test sentences, 3 seeds, 2 independent reference sets. Native output, no edits.
Run with the MLX-Audio venv (mlx-audio 0.5.8). Holds the shared .render.lock while the model runs."""
from pathlib import Path
import os, sys, json, time, hashlib, fcntl
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false')
import numpy as np, soundfile as sf, mlx.core as mx
from mlx_audio.tts.utils import load_model
import importlib.metadata as md

D = Path(__file__).resolve().parent; O = D / 'clones'; O.mkdir(exist_ok=True)
MODEL = Path.home() / '.cache/huggingface/hub/models--mlx-community--Qwen3-TTS-12Hz-1.7B-Base-bf16/snapshots/a6eb4f68e4b056f1215157bb696209bc82a6db48'
LOCK = Path(os.environ.get('RENDER_LOCK', '/tmp/titl-render.lock'))
SENTENCES = [
    ('s1', "Before you send money, call them back on a number you already know."),
    ('s2', "This sentence was never spoken by me. A computer generated it from a short recording."),
    ('s3', "The weather in Seattle was surprisingly sunny on Tuesday afternoon."),
    ('s4', "Voice cloning can help people who lost their voice, but it needs consent."),
]
SEEDS = [11, 22, 33]
refs = json.loads((D / 'refs/REFS.json').read_text())['conditions']
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
mx.set_memory_limit(18 * 1024**3); mx.set_cache_limit(1024**3)
with LOCK.open('a') as lk:
    fcntl.flock(lk, fcntl.LOCK_EX)
    t0 = time.time(); model = load_model(MODEL, trust_remote_code=False, lazy=True); print('LOADED', round(time.time() - t0, 1), flush=True)
    for cond, ref in refs.items():
        assert sha(ref['audio']) == ref['sha256']
        for sid, text in SENTENCES:
            for seed in SEEDS:
                out = O / f'{cond}__{sid}__seed{seed}.wav'; rec = out.with_suffix('.json')
                if out.exists() and rec.exists(): continue
                mx.random.seed(seed)
                params = dict(ref_audio=ref['audio'], ref_text=ref['text'], temperature=.9, speed=1., lang_code='english',
                              max_tokens=600, top_k=50, top_p=1., repetition_penalty=1.5, stream=False, verbose=False)
                b = time.time(); rs = list(model.generate(text=text, **params)); a = np.concatenate([np.asarray(r.audio, np.float32).squeeze() for r in rs])
                sf.write(out, a, rs[0].sample_rate, subtype='FLOAT')
                rec.write_text(json.dumps({'condition': cond, 'sentence': sid, 'text': text, 'seed': seed, 'ref_seconds': ref['seconds'], 'ref_sha256': ref['sha256'],
                    'model': 'Qwen3-TTS-12Hz-1.7B-Base-bf16', 'snapshot': MODEL.name, 'mlx_audio': md.version('mlx-audio'), 'mlx': md.version('mlx'),
                    'params': {k: v for k, v in params.items() if k != 'ref_audio'}, 'seconds': len(a) / rs[0].sample_rate, 'sample_rate': rs[0].sample_rate,
                    'sha256': sha(out), 'synthesis_seconds': time.time() - b, 'native_unedited': True}, indent=1))
                print(cond, sid, seed, round(len(a) / rs[0].sample_rate, 2), round(time.time() - b, 1), flush=True)
                mx.clear_cache()
print('DONE')
