#!/bin/bash
# usage: GOOGLE_API_KEY=... ./run_matrix.sh <model>   (4 trials x clean/inject)
cd "$(dirname "$0")"
m=$1
for t in 1 2 3 4; do for task in clean inject; do
  .venv/bin/python run_one.py "$m" "$task" "$t" "runs/$m/$task-$t" 2>&1 | tail -1 >> "matrix-$m.log"
done; done
echo DONE >> "matrix-$m.log"
