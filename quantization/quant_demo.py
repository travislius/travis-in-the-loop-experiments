"""Model quantization demo (Travis in the Loop).

One open model (Qwen/Qwen2.5-1.5B-Instruct) at bf16, 8-, 4-, 3- and 2-bit (MLX affine,
group size 64), measured on this Mac:
  * on-disk size of the weight files
  * peak memory while generating
  * generation speed (tokens/s), N repeated runs
  * perplexity on a fixed slice of WikiText-2 (test split)
  * a fixed 20-question factual QA set (greedy, answer substring match)
plus a hand-worked rounding example on real weights.

Usage:
  python quant_demo.py convert          # make the quantized copies with mlx_lm.convert
  python quant_demo.py rounding         # hand-worked example -> results/rounding.json
  python quant_demo.py quality          # perplexity + QA      -> results/quality-<variant>.json
  python quant_demo.py speed RUN_ID     # timing (run under an exclusive lock) -> results/speed-<run>.json
No API keys. Weights are downloaded from Hugging Face, never committed.
"""
import sys, json, time, hashlib, platform, subprocess, math
from pathlib import Path
import numpy as np
import mlx.core as mx
import mlx_lm
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

HF_ID = 'Qwen/Qwen2.5-1.5B-Instruct'
D = Path(__file__).resolve().parent
M = D / 'models'
R = D / 'results'; R.mkdir(exist_ok=True)
VARIANTS = [('bf16', None), ('q8', 8), ('q4', 4), ('q3', 3), ('q2', 2)]
GROUP = 64
PPL_WINDOWS, PPL_LEN = 40, 512
PROMPT = 'Explain in a few paragraphs how a refrigerator keeps food cold.'
GEN_TOKENS = 256

QA = [
    ('What is the capital of France?', ['paris']),
    ('What is the capital of Japan?', ['tokyo']),
    ('What is the chemical symbol for gold?', ['au']),
    ('How many continents are there on Earth?', ['seven', '7']),
    ('Who wrote "Romeo and Juliet"?', ['shakespeare']),
    ('What planet is known as the Red Planet?', ['mars']),
    ('What is the largest ocean on Earth?', ['pacific']),
    ('What gas do plants absorb from the air for photosynthesis?', ['carbon dioxide', 'co2', 'co₂']),
    ('What is 12 multiplied by 12?', ['144']),
    ('What is the boiling point of water at sea level in degrees Celsius?', ['100']),
    ('Who painted the Mona Lisa?', ['leonardo', 'da vinci']),
    ('What is the smallest prime number?', ['2', 'two']),
    ('In which country are the pyramids of Giza?', ['egypt']),
    ('What is the hardest natural substance?', ['diamond']),
    ('How many legs does a spider have?', ['eight', '8']),
    ('What is the square root of 81?', ['9', 'nine']),
    ('Which element has the atomic number 1?', ['hydrogen']),
    ('What language is primarily spoken in Brazil?', ['portuguese']),
    ('Who developed the theory of relativity?', ['einstein']),
    ('What is the freezing point of water in degrees Fahrenheit?', ['32']),
]


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def env():
    return {'mlx': mx.__version__, 'mlx_lm': mlx_lm.__version__, 'python': platform.python_version(),
            'machine': subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], capture_output=True, text=True).stdout.strip(),
            'ram_bytes': int(subprocess.run(['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True).stdout),
            'macos': platform.mac_ver()[0], 'time': time.strftime('%Y-%m-%dT%H:%M:%S%z')}


def path(v):
    return M / v


def disk(v):
    files = sorted(path(v).glob('*.safetensors'))
    return {'bytes': sum(f.stat().st_size for f in files), 'files': {f.name: sha(f) for f in files}}


def convert():
    from mlx_lm import convert as cv
    for v, bits in VARIANTS:
        if path(v).exists():
            continue
        from huggingface_hub import snapshot_download
        kw = dict(hf_path=snapshot_download(HF_ID, allow_patterns=["*.json","*.safetensors","*.txt"]), mlx_path=str(path(v)))
        if bits:
            kw.update(quantize=True, q_bits=bits, q_group_size=GROUP)
        else:
            kw.update(dtype='bfloat16')
        cv(**kw)
    out = {v: disk(v) for v, _ in VARIANTS}
    out['_env'] = env()
    (R / 'convert.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v['bytes'] for k, v in out.items() if not k.startswith('_')}))


def rounding():
    """Hand-worked 4-bit affine example on 8 real weights of layer 0 q_proj (bf16 model)."""
    import mlx.nn as nn
    model, _ = load(str(path('bf16')))
    W = model.model.layers[0].self_attn.q_proj.weight  # (out, in)
    group = np.array(W[0, :GROUP].astype(mx.float32))
    # MLX's own 4-bit affine quantizer: w ~= scale * code + bias, code in 0..15
    wq, s, b = mx.quantize(mx.array(group[None, :]), group_size=GROUP, bits=4)
    mlx_back = np.array(mx.dequantize(wq, s, b, group_size=GROUP, bits=4))[0]
    scale, bias = float(s[0, 0]), float(b[0, 0])
    lo, hi = float(group.min()), float(group.max())
    codes = np.clip(np.round((group - bias) / scale), 0, 15).astype(int)
    back = codes * scale + bias
    out = {'tensor': 'model.layers.0.self_attn.q_proj.weight[0, 0:64]', 'bits': 4, 'levels': 16,
           'min': lo, 'max': hi, 'scale': scale, 'bias': bias, 'first8': {
               'original': group[:8].tolist(), 'code': codes[:8].tolist(), 'restored': back[:8].tolist(),
               'error': (back[:8] - group[:8]).tolist()},
           'group_mean_abs_error': float(np.abs(back - group).mean()),
           'group_mean_abs_weight': float(np.abs(group).mean()),
           'mlx_quantizer_max_diff_vs_hand': float(np.abs(mlx_back - back).max()),
           'storage_bits_per_weight_q4_g64': 4 + 32 / GROUP,  # bf16 scale + bf16 bias per group
           '_env': env()}
    (R / 'rounding.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out['first8'], indent=1))


def wikitext_tokens(tok):
    from huggingface_hub import hf_hub_download
    import pyarrow.parquet as pq
    p = hf_hub_download('Salesforce/wikitext', 'wikitext-2-raw-v1/test-00000-of-00001.parquet', repo_type='dataset')
    text = '\n'.join(pq.read_table(p).column('text').to_pylist())
    ids = tok.encode(text)
    return ids, {'file': p, 'sha256': sha(p), 'tokens': len(ids)}


def quality(variants):
    for v in variants:
        model, tok = load(str(path(v)))
        ids, src = wikitext_tokens(tok)
        nll, n = 0.0, 0
        for w in range(PPL_WINDOWS):
            x = mx.array(ids[w * PPL_LEN:(w + 1) * PPL_LEN])[None]
            logits = model(x[:, :-1]).astype(mx.float32)
            lp = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
            t = mx.take_along_axis(lp, x[:, 1:, None], axis=-1)
            nll -= float(t.sum()); n += PPL_LEN - 1
        ppl = math.exp(nll / n)
        qa = []
        for q, ans in QA:
            msgs = [{'role': 'user', 'content': q + ' Answer in a few words.'}]
            prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
            txt = ''.join(r.text for r in stream_generate(model, tok, prompt, max_tokens=24, sampler=make_sampler(temp=0.0)))
            qa.append({'q': q, 'answer': txt.strip(), 'correct': any(a in txt.lower() for a in ans)})
        out = {'variant': v, 'perplexity': ppl, 'ppl_tokens_scored': n, 'ppl_windows': PPL_WINDOWS, 'ppl_window_len': PPL_LEN,
               'wikitext': src, 'qa_correct': sum(x['correct'] for x in qa), 'qa_total': len(qa), 'qa': qa, '_env': env()}
        (R / f'quality-{v}.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
        print(v, round(ppl, 3), out['qa_correct'], '/', len(qa), flush=True)
        del model; mx.clear_cache()


def speed(run_id, reps=3):
    res = {'run': run_id, 'prompt': PROMPT, 'max_tokens': GEN_TOKENS, 'sampler': 'greedy', 'variants': {}, '_env': env()}
    for v, _ in VARIANTS:
        model, tok = load(str(path(v)))
        prompt = tok.apply_chat_template([{'role': 'user', 'content': PROMPT}], add_generation_prompt=True, tokenize=False)
        list(stream_generate(model, tok, prompt, max_tokens=16))  # warm-up
        reps_out = []
        for i in range(reps):
            mx.reset_peak_memory()
            last = None
            for last in stream_generate(model, tok, prompt, max_tokens=GEN_TOKENS, sampler=make_sampler(temp=0.0)):
                pass
            reps_out.append({'gen_tps': last.generation_tps, 'prompt_tps': last.prompt_tps, 'gen_tokens': last.generation_tokens,
                             'peak_memory_gb': last.peak_memory})
        res['variants'][v] = reps_out
        print(v, [round(r['gen_tps'], 1) for r in reps_out], round(reps_out[-1]['peak_memory_gb'], 3), flush=True)
        del model; mx.clear_cache()
    (R / f'speed-{run_id}.json').write_text(json.dumps(res, indent=1))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'convert': convert()
    elif cmd == 'rounding': rounding()
    elif cmd == 'quality': quality(sys.argv[2:] or [v for v, _ in VARIANTS])
    elif cmd == 'speed': speed(sys.argv[2])
