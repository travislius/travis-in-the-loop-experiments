#!/bin/bash
# Usage: ./run.sh <A|B|C> <rep>
set -e; cd "$(dirname "$0")"
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-$(security find-generic-password -a deepseek -s DEEPSEEK_API_KEY -w)}"
[ -d agent-bin ] && export PATH="$PWD/agent-bin:$PATH"
exec .venv/bin/python run_one.py "$@"
