#!/bin/bash
# Hard tier added after the first 8 tasks all resolved: 3 tasks x 2 models x 5 reps = 30 attempts.
cd "$(dirname "$0")"; mkdir -p runs
for r in 1 2 3 4 5; do for m in deepseek-flash deepseek-v4-pro; do for t in cron expr glob; do ./run.sh $t $m $r 2>runs/$t-${m#deepseek-}-r$r.stderr.log & done; done; wait; done
echo HARD_DONE
