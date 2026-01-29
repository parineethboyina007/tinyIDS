# defense/policy_promoter.py

import os
import json
from datetime import datetime
from typing import Optional

POLICY_DIR = "governance/adaptive_policies"
DECAY_DIR = "governance/policy_decay"
PROMOTION_LOG = "governance/policy_promotions.json"

PROMOTION_CLEAN_THRESHOLD = 10   # must match rewidener threshold

# ==================================================
# SAFE JSON HELPERS
# ==================================================

def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except Exception:
        return default


def _save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ==================================================
# STEP-63 — CANARY PROMOTION ENGINE
# ==================================================

def maybe_promote_canary_rule(
    tenant: str,
    rule_id: str,
) -> Optional[dict]:
    """
    STEP-63 — Promote canary-rewidened rule to active.

    Conditions:
    • rule.rewidening_mode == "canary"
    • rule is rewidened
    • zero false positives
    • sustained clean traffic
    """

    policy_path = os.path.join(POLICY_DIR, f"{tenant}.json")
    decay_path = os.path.join(DECAY_DIR, f"{tenant}__{rule_id}.json")

    if not os.path.exists(policy_path):
        return None

    policy = _load_json(policy_path, {})
    rules = policy.get("rules", [])

    decay = _load_json(decay_path, {})
    false_positives = decay.get("false_positives", 0)
    clean_events = decay.get("clean_events", 0)

    if false_positives > 0 or clean_events < PROMOTION_CLEAN_THRESHOLD:
        return None

    now = datetime.utcnow().isoformat()

    for rule in rules:
        if rule.get("id") != rule_id:
            continue

        # ----------------------------------
        # REQUIRE CANARY MODE
        # ----------------------------------

        if rule.get("rewidening_mode") != "canary":
            return None

        # ----------------------------------
        # PROMOTE RULE
        # ----------------------------------

        rule.pop("rewidening_mode", None)
        rule["promoted_to_active_at"] = now

        policy["last_updated"] = now
        _save_json(policy_path, policy)

        # ----------------------------------
        # AUDIT LOG
        # ----------------------------------

        log = _load_json(PROMOTION_LOG, [])
        log.append({
            "tenant": tenant,
            "rule_id": rule_id,
            "action": "promoted_to_active",
            "reason": "canary_stability_confirmed",
            "timestamp": now,
        })
        _save_json(PROMOTION_LOG, log)

        return rule

    return None