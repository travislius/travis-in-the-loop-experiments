#!/bin/bash
# Usage: ./run.sh <task> <mode> <rep>
# Confinement: DeepSeek Harness's own Seatbelt sandbox in workspace-write mode (patches/confine*.yml).
# (An outer sandbox-exec cannot be used: macOS Seatbelt profiles do not nest, which broke the bash tool.)
set -e; cd "$(dirname "$0")"
: "${DEEPSEEK_API_KEY:?Set DEEPSEEK_API_KEY in your environment}"
export DEEPSEEK_API_KEY
# Agents get Python 3.11 as python3 (system python3 is 3.9, which cannot import PEP 604 hints).
export PATH="$PWD/agent-bin:$PATH"
exec .venv/bin/python run_one.py "$@"
