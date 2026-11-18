"""Transparent stdio tap: launches server.py and logs every raw JSON-RPC line to wire.log."""
import subprocess, sys, threading, time, pathlib
log = open(pathlib.Path(__file__).with_name("wire.log"), "a", buffering=1)
p = subprocess.Popen([sys.executable, str(pathlib.Path(__file__).with_name("server.py"))], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
def pump(src, dst, tag):
    for line in iter(src.readline, b""):
        log.write(f"{time.time():.3f} {tag} {line.decode().rstrip()}\n"); dst.write(line); dst.flush()
    try: dst.close()
    except Exception: pass
t = threading.Thread(target=pump, args=(p.stdout, sys.stdout.buffer, "SERVER->CLIENT"), daemon=True); t.start()
pump(sys.stdin.buffer, p.stdin, "CLIENT->SERVER"); p.wait(); t.join(2)
