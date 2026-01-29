# defense/policy_decay_engine.py

import os
import json
from datetime import datetime

DECAY_DIR = "governance/policy_decay"
os.makedirs(DECAY_DIR, exist_ok=True)

FALSE_POSITIVE_THRESHOLD = 3


def _path(tenant: str, rule_id: str) -> str:
    return os.path.join(DECAY_DIR, f"{tenant}__{rule_id}.json")


def record_enforcement(tenant: str, rule_id: str, blocked: bool):
    """
    Tracks false positives for adaptive rules.
    """

    path = _path(tenant, rule_id)

    if os.path.exists(path):
        with open(path) as f:
            state = json.load(f)
    else:
        state = {
            "tenant": tenant,
            "rule_id": rule_id,
            "false_positives": 0,
            "first_seen": datetime.utcnow().isoformat(),
        }

    if blocked is False:
        state["false_positives"] += 1

    state["last_updated"] = datetime.utcnow().isoformat()

    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def get_decay_state(tenant: str, rule_id: str) -> dict | None:
    path = _path(tenant, rule_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)