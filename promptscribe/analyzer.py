# promptscribe/analyzer.py
import os
import json
import time
import uuid
from promptscribe.config import CONFIG
from promptscribe.utils import safe_write_json

ANALYSIS_DIR = CONFIG["paths"]["analysis"]
os.makedirs(ANALYSIS_DIR, exist_ok=True)

def run_analysis(session_paths, merge=False):
    """
    session_paths: tuple/list of session file paths or basenames.
    merge: if True create single combined analysis, else create per-session analysis.
    """
    # normalize inputs
    paths = []
    for p in session_paths:
        if os.path.isabs(p) and os.path.exists(p):
            paths.append(p)
            continue
        alt = os.path.join(CONFIG["paths"]["logs"], p)
        if os.path.exists(alt):
            paths.append(alt)
            continue
        # try with extension
        if not p.endswith(".jsonl"):
            alt2 = alt + ".jsonl"
            if os.path.exists(alt2):
                paths.append(alt2)
                continue

    if not paths:
        print("No valid session files found for analysis.")
        return

    if merge:
        _create_merged_analysis(paths)
    else:
        for p in paths:
            _create_single_analysis(p)

def _create_single_analysis(path):
    aid = f"A-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    out_json = os.path.join(ANALYSIS_DIR, f"{aid}.json")
    meta_json = os.path.join(ANALYSIS_DIR, f"{aid}.meta.json")
    # simple mock analysis: count lines, extract first/last ts
    count = 0
    first_ts = None
    last_ts = None
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            try:
                obj = json.loads(ln)
                ts = obj.get("ts")
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
                count += 1
            except Exception:
                continue
    summary = f"Session {os.path.basename(path)}: {count} output events from {first_ts} to {last_ts}"
    analysis = {"analysis_id": aid, "summary": summary, "input": [path]}
    safe_write_json(out_json, analysis)
    safe_write_json(meta_json, {"analysis_id": aid, "input_sessions": [path], "output_file": out_json})
    print("Saved analysis:", out_json)

def _create_merged_analysis(paths):
    aid = f"A-{time.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6]}"
    out_json = os.path.join(ANALYSIS_DIR, f"{aid}.json")
    meta_json = os.path.join(ANALYSIS_DIR, f"{aid}.meta.json")
    total = 0
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            for _ in f:
                total += 1
    summary = f"Merged analysis of {len(paths)} sessions. {total} total events."
    analysis = {"analysis_id": aid, "summary": summary, "input": paths}
    safe_write_json(out_json, analysis)
    safe_write_json(meta_json, {"analysis_id": aid, "input_sessions": paths, "output_file": out_json})
    print("Saved merged analysis:", out_json)
