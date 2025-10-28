# promptscribe/parser.py
import json
import os
from typing import List, Dict, Any

def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load all JSONL lines safely."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing log file: {path}")
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                # corrupted or partial line
                continue
    return events


def parse_session(path: str) -> Dict[str, Any]:
    """Parse session JSONL into structured form."""
    events = load_jsonl(path)

    commands = []
    current_cmd = {"input": "", "output": ""}
    last_kind = None

    for evt in events:
        kind = evt.get("kind")
        data = evt.get("data", "")
        if kind == "out":
            # Accumulate output until new input appears
            current_cmd["output"] += data
        elif kind == "in":
            # Save previous command if it exists
            if current_cmd["input"] or current_cmd["output"]:
                commands.append(current_cmd)
            current_cmd = {"input": data, "output": ""}
        last_kind = kind

    # Add final command if exists
    if current_cmd["input"] or current_cmd["output"]:
        commands.append(current_cmd)

    # Compute session summary
    summary = {
        "total_events": len(events),
        "total_commands": len(commands),
        "log_path": path,
    }

    return {"summary": summary, "commands": commands}


def print_summary(parsed: Dict[str, Any]):
    """Print human-readable summary of a parsed session."""
    s = parsed["summary"]
    print(f"\nSession Summary:")
    print(f"  File: {s['log_path']}")
    print(f"  Events: {s['total_events']}")
    print(f"  Commands: {s['total_commands']}\n")
    print("Sample commands:")
    for c in parsed["commands"][:3]:
        inp = c["input"].strip().replace("\n", " ")
        out = (c["output"][:60] + "...") if len(c["output"]) > 60 else c["output"]
        print(f"  > {inp}\n    {out}\n")
