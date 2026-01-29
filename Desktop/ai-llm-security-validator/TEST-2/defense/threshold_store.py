# defense/threshold_store.py

import os
import json
from datetime import datetime

BASE_DIR = "policies/thresholds"
ACTIVE_FILE = os.path.join(BASE_DIR, "active.json")
CANARY_FILE = os.path.join(BASE_DIR, "canary.json")

os.makedirs(BASE_DIR, exist_ok=True)

DEFAULT = {
    "risk_block_threshold": 0.8,
    "severity_floor": "High",
    "last_updated": None,
}

def _load(path):
    if not os.path.exists(path):
        return DEFAULT.copy()
    with open(path) as f:
        return json.load(f)

def _save(path, data):
    data["last_updated"] = datetime.utcnow().isoformat()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_thresholds(mode="active"):
    return _load(CANARY_FILE if mode == "canary" else ACTIVE_FILE)

def save_thresholds(mode, thresholds):
    _save(CANARY_FILE if mode == "canary" else ACTIVE_FILE, thresholds)