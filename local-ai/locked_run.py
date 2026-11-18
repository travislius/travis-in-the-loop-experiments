#!/usr/bin/env python3
"""Run run_experiment.py stages while holding the shared local-GPU TTS lock, so sibling TTS jobs
queue instead of competing for the GPU during measurements (renders by other processes can still run;
each bench record stores a snapshot of busy processes)."""
import fcntl, subprocess, sys, time
from pathlib import Path
L = open(Path.home() / ".hermes/cache/scratch/ftf-tts-generation.lock", "a")
t = time.monotonic()
while True:
    try: fcntl.flock(L, fcntl.LOCK_EX | fcntl.LOCK_NB); break
    except BlockingIOError: time.sleep(5)
print("LOCK after", round(time.monotonic() - t), "s", flush=True)
try:
    for stage in sys.argv[1].split(","):
        subprocess.run([sys.executable, str(Path(__file__).parent / "run_experiment.py"), stage] + sys.argv[2:], check=True)
finally:
    fcntl.flock(L, fcntl.LOCK_UN)
