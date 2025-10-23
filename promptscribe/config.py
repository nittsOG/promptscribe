# promptscribe/config.py
import os
import pathlib
import yaml
from promptscribe.constants import DEFAULT_CONFIG

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / DEFAULT_CONFIG

if not CFG_PATH.exists():
    raise FileNotFoundError(f"Missing config file: {CFG_PATH}")

with open(CFG_PATH, "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

# Normalize paths and ensure only parent directories exist
for key, val in CONFIG.get("paths", {}).items():
    p = (ROOT / val).resolve() if not os.path.isabs(val) else pathlib.Path(val)
    CONFIG["paths"][key] = str(p)
    parent = p.parent  # only ensure directory, not the file itself
    try:
        parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
