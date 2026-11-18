#!/bin/bash
# Resume after Q4/Qwen hash verification: measure the ready models now, then wait for Q8.
cd "$(dirname "$0")"; PY=/usr/bin/python3
$PY run_experiment.py env
for k in flint-q4 qwen32-q4; do $PY locked_run.py bench,memory $k || exit 1; done
$PY locked_run.py ppl flint-q4 || exit 1
f=Flint-Q8_0.gguf; size=42350359520; oid=8a257b63c0fd1611947db267e3fa84ac3de0ed6f4c43255612236afd226a4f93
while [ "$(stat -f %z models/$f)" != "$size" ]; do sleep 30; done
got=$(shasum -a 256 models/$f | cut -d' ' -f1); echo "$f $got expected $oid" >> models/SHA256-VERIFY.txt
[ "$got" = "$oid" ] || { echo "HASH MISMATCH $f"; exit 1; }
$PY run_experiment.py env
$PY locked_run.py bench,memory,ppl flint-q8 || exit 1
echo EXPERIMENT_DONE
