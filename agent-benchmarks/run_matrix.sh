#!/bin/bash
# 8 tasks x 2 models x 5 reps = 80 attempts; 8 at a time.
cd "$(dirname "$0")"; mkdir -p runs
for r in 1 2 3 4 5; do for m in deepseek-flash deepseek-v4-pro; do for t in slugify overlap lru money merge bucket roman semver; do ./run.sh $t $m $r 2>runs/$t-${m#deepseek-}-r$r.stderr.log & done; wait; done; done
echo MATRIX_DONE
