#!/bin/bash
# 3 conditions x 8 reps, conditions interleaved, 3 runs at a time.
cd "$(dirname "$0")"
for r in 1 2 3 4 5 6 7 8; do
  for c in A B C; do ./run.sh $c $r 2>runs/$c-r$r.stderr.log & done
  wait
done
echo MATRIX_DONE
