# defense/policy_drift_store.py

import os
import json
from datetime import datetime

DRIFT_DIR = "governance/policy_drift"
os.makedirs(DRIFT_DIR, exist_ok=True)


def _path(tenant: str, rule_id: str) -> str:
    return os.path.join(DRIFT_DIR, f"{tenant}__{rule_id}.json")


def load_drift_state(tenant: str, rule_id: str) -> dict:
    path = _path(tenant, rule_id)
    if not os.path.exists(path):
        return {
            "tenant": tenant,
            "rule_id": rule_id,
            "baseline": {
                "blocked": 0,
                "clean": 0,
                "false_positives": 0,
            },
            "recent": {
                "blocked": 0,
                "clean": 0,
                "false_positives": 0,
            },
            "last_updated": None,
        }
    with open(path) as f:
        return json.load(f)


def save_drift_state(state: dict):
    state["last_updated"] = datetime.utcnow().isoformat()
    path = _path(state["tenant"], state["rule_id"])
    with open(path, "w") as f:
        json.dump(state, f, indent=2)