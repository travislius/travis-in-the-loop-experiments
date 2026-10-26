"""Aggregate raw results into results/summary.json."""
import json,statistics as st
from pathlib import Path
R=Path(__file__).resolve().parent/'results'
cv=json.loads((R/'convert.json').read_text());runs=[json.loads(p.read_text()) for p in sorted(R.glob('speed-run*.json'))]
out={'model':'Qwen/Qwen2.5-1.5B-Instruct','speed_runs':len(runs),'variants':{}}
for v in ['bf16','q8','q4','q3','q2']:
    q=json.loads((R/f'quality-{v}.json').read_text());tps=[r['gen_tps'] for x in runs for r in x['variants'][v]];mem=[r['peak_memory_gb'] for x in runs for r in x['variants'][v]]
    toks=[r['gen_tokens'] for x in runs for r in x['variants'][v]]
    out['variants'][v]={'disk_bytes':cv[v]['bytes'],'disk_gb':cv[v]['bytes']/1e9,'size_vs_bf16':cv[v]['bytes']/cv['bf16']['bytes'],'gen_tps_median':st.median(tps),'gen_tps_min':min(tps),'gen_tps_max':max(tps),'n_timings':len(tps),'gen_tokens':sorted(set(toks)),'peak_mem_gb_max':max(mem),'perplexity':q['perplexity'],'qa':f"{q['qa_correct']}/{q['qa_total']}"}
b=out['variants']['bf16']
for v,x in out['variants'].items():x['speedup_vs_bf16']=x['gen_tps_median']/b['gen_tps_median']
(R/'summary.json').write_text(json.dumps(out,indent=1));print(json.dumps(out,indent=1))
