# defense/policy_rollback_engine.py

import json
import os
from datetime import datetime
from defense.policy_decay_engine import get_decay_state

POLICY_DIR = "governance/adaptive_policies"
ROLLBACK_LOG = "governance/policy_rollbacks.json"
MAX_FALSE_POSITIVES = 3


def evaluate_rollback(tenant: str, rule_id: str):
    """
    Rolls back adaptive policy rules that misfire.
    """

    decay = get_decay_state(tenant, rule_id)
    if not decay:
        return

    if decay["false_positives"] < MAX_FALSE_POSITIVES:
        return

    policy_path = os.path.join(POLICY_DIR, f"{tenant}.json")
    if not os.path.exists(policy_path):
        return

    with open(policy_path) as f:
        policy = json.load(f)

    rules_before = len(policy.get("rules", []))
    policy["rules"] = [
        r for r in policy.get("rules", [])
        if r.get("id") != rule_id
    ]

    if len(policy["rules"]) == rules_before:
        return

    policy["last_updated"] = datetime.utcnow().isoformat()

    with open(policy_path, "w") as f:
        json.dump(policy, f, indent=2)

    _log_rollback(tenant, rule_id, decay)


def _log_rollback(tenant: str, rule_id: str, decay: dict):
    entry = {
        "tenant": tenant,
        "rule_id": rule_id,
        "rolled_back_at": datetime.utcnow().isoformat(),
        "false_positives": decay["false_positives"],
    }

    if os.path.exists(ROLLBACK_LOG):
        with open(ROLLBACK_LOG) as f:
            log = json.load(f)
    else:
        log = []

    log.append(entry)

    with open(ROLLBACK_LOG, "w") as f:
        json.dump(log, f, indent=2)