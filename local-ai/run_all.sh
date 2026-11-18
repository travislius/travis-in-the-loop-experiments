#!/bin/bash
# Wait for complete, hash-verified downloads, then measure each model under the shared GPU lock.
cd "$(dirname "$0")"
PY=/usr/bin/python3
want() { python3 -c "
import json,sys
for l in open('models/HF-TREES.json'):
  for f in json.loads(l):
    if f['path']=='$1':print(f['size'],f['lfs']['oid'])"; }
for f in Flint-Q4_K_M.gguf Qwen3-32B-Q4_K_M.gguf Flint-Q8_0.gguf; do
  read size oid <<< "$(want $f)"
  while [ "$(stat -f %z models/$f 2>/dev/null)" != "$size" ]; do sleep 30; done
  got=$(shasum -a 256 models/$f | cut -d' ' -f1)
  echo "$f $got expected $oid" | tee -a models/SHA256-VERIFY.txt
  [ "$got" = "$oid" ] || { echo "HASH MISMATCH $f"; exit 1; }
done
echo DOWNLOADS_VERIFIED
$PY run_experiment.py env
for k in flint-q4 qwen32-q4 flint-q8; do $PY locked_run.py bench,memory $k || exit 1; done
for k in flint-q4 flint-q8; do $PY locked_run.py ppl $k || exit 1; done
echo EXPERIMENT_DONE
