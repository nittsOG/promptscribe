# promptscribe/logger.py
import os
import sys
import json
import time
import uuid
import datetime
from promptscribe.config import CONFIG
from promptscribe.utils import safe_write_json

OUT_DIR = CONFIG["paths"]["logs"]
META_DIR = CONFIG["paths"]["metadata"]

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(META_DIR, exist_ok=True)

def _make_session_paths(name=None):
    ts = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%SZ")
    sid = f"S-{ts}-{uuid.uuid4().hex[:6]}"
    safe_name = name.replace(" ", "_") if name else None
    fname = f"{sid}{('__' + safe_name) if safe_name else ''}.jsonl"
    meta = f"{sid}.meta.json"
    return sid, os.path.join(OUT_DIR, fname), os.path.join(META_DIR, meta)

def start_session(name=None):
    sid, outpath, metapath = _make_session_paths(name)
    start_ts = time.time()
    meta = {
        "session_id": sid,
        "name": name,
        "start_ts": start_ts,
        "file": outpath,
        "hostname": os.uname().nodename if hasattr(os, "uname") else os.environ.get("COMPUTERNAME")
    }
    safe_write_json(metapath, meta)
    print(f"Recording session {sid}")
    print(f"Output -> {outpath}")
    try:
        if os.name == "nt":
            _start_windows_session(outpath)
        else:
            _start_unix_session(outpath)
    finally:
        meta["end_ts"] = time.time()
        safe_write_json(metapath, meta)
        print(f"Session {sid} finished. Metadata -> {metapath}")

# Unix PTY implementation
def _start_unix_session(outpath):
    import os as _os, pty, select
    master, slave = pty.openpty()
    pid = _os.fork()
    if pid == 0:
        # child
        _os.setsid()
        _os.dup2(slave, 0)
        _os.dup2(slave, 1)
        _os.dup2(slave, 2)
        shell = _os.environ.get("SHELL", "/bin/bash")
        _os.execvp(shell, [shell])
    else:
        # parent: recorder
        with open(outpath, "a", encoding="utf-8") as f:
            try:
                while True:
                    r, _, _ = select.select([master], [], [])
                    if master in r:
                        data = _os.read(master, 4096)
                        if not data:
                            break
                        ts = time.time()
                        f.write(json.dumps({"ts": ts, "out": data.decode(errors="replace")}) + "\n")
                        f.flush()
                        # echo to user's terminal
                        os.write(1, data)
            except KeyboardInterrupt:
                pass

# Windows fallback using wexpect
def _start_windows_session(outpath):
    try:
        import wexpect
    except Exception:
        print("wexpect not installed. Install with: pip install wexpect")
        return
    shell = os.environ.get("COMSPEC", "cmd.exe")
    child = wexpect.spawn(shell, timeout=0.1)
    with open(outpath, "a", encoding="utf-8") as f:
        try:
            while True:
                try:
                    out = child.read_nonblocking(size=4096, timeout=0.1)
                except Exception:
                    out = ""
                if out:
                    ts = time.time()
                    f.write(json.dumps({"ts": ts, "out": out}) + "\n")
                    f.flush()
                    sys.stdout.write(out)
        except KeyboardInterrupt:
            try:
                child.terminate()
            except Exception:
                pass
