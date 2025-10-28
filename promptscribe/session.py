# promptscribe/session.py
import os
import time
import uuid
import json
from promptscribe.config import CONFIG
from promptscribe.utils import safe_write_json
from promptscribe import recorder, db

LOG_DIR = CONFIG["paths"]["logs"]
META_DIR = CONFIG["paths"]["metadata"]

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(META_DIR, exist_ok=True)

def _make_paths(name=None):
    ts = time.strftime("%Y%m%d_%H%M%SZ", time.gmtime())
    sid = f"S-{ts}-{uuid.uuid4().hex[:6]}"
    safe_name = None
    if name:
        safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)[:64]
    fname = f"{sid}{('__' + safe_name) if safe_name else ''}.jsonl"
    meta_name = f"{sid}.meta.json"
    return sid, os.path.join(LOG_DIR, fname), os.path.join(META_DIR, meta_name)

def start(name=None, user_description=None, register_db=True):
    sid, outpath, metapath = _make_paths(name)
    meta = {
        "session_id": sid,
        "name": name,
        "user_description": user_description,
        "start_ts": time.time(),
        "file": outpath
    }
    safe_write_json(metapath, meta)
    print(f"Starting session {sid}")
    print(f"Log file: {outpath}")
    # run recorder (blocking) until shell exit
    recorder.record(outpath)
    # finalize metadata
    meta["end_ts"] = time.time()
    safe_write_json(metapath, meta)
    print(f"Session finished. Metadata: {metapath}")
    # register in DB if requested
    if register_db:
        try:
            db.insert_session(metapath)
            print("Session indexed in DB.")
        except Exception as e:
            print("Failed to index session in DB:", e)
    return sid, outpath, metapath
