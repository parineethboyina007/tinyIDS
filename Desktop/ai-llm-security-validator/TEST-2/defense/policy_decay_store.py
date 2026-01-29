# defense/policy_decay_store.py

import os
import json
from datetime import datetime

DECAY_DIR = "governance/policy_decay"
os.makedirs(DECAY_DIR, exist_ok=True)

DECAY_THRESHOLD = 3  # rollback trigger


def _path(tenant: str, rule_id: str) -> str:
    return os.path.join(DECAY_DIR, f"{tenant}__{rule_id}.json")


def record_false_positive(tenant: str, rule_id: str) -> dict:
    now = datetime.utcnow().isoformat()
    path = _path(tenant, rule_id)

    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
    else:
        data = {
            "tenant": tenant,
            "rule_id": rule_id,
            "false_positives": 0,
            "first_seen": now,
        }

    data["false_positives"] += 1
    data["last_updated"] = now

    with open(path, "w") as f:
        json.dump(data, f, indent=2)

    return data