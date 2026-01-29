# defense/rollback_policy.py

import json
import os

POLICY_PATH = "governance/rollback_policy.json"

DEFAULT_POLICY = {
    "mode": "recommend",
    "approvals_required": {
        "canary": 1,
        "active": 2
    }
}

def load_policy() -> dict:
    if not os.path.exists(POLICY_PATH):
        return DEFAULT_POLICY.copy()

    with open(POLICY_PATH) as f:
        return json.load(f)