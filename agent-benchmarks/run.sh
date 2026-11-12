#!/bin/bash
# Usage: ./run.sh <task> <model> <rep>
set -e; cd "$(dirname "$0")"
export DEEPSEEK_API_KEY="$(security find-generic-password -a deepseek -s DEEPSEEK_API_KEY -w)"
export PATH="$PWD/agent-bin:$PATH"
exec .venv/bin/python run_one.py "$@"
