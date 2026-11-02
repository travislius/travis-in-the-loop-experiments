#!/bin/bash
cd "$(dirname "$0")"
for rep in 1 2 3 4 5; do for task in calc logs; do for mode in minimal standard ptc; do
  echo "== $task $mode r$rep"; ./run.sh $task $mode $rep 2>runs/$task-$mode-r$rep.stderr.log | tail -1 || echo "FAILED $task $mode $rep"
done; done; done
echo HARD_DONE
