# defense/policy_demoter.py

import os
import json
from datetime import datetime
from typing import Optional

# ==================================================
# PATHS
# ==================================================

POLICY_DIR = "governance/adaptive_policies"
HEALTH_DIR = "governance/policy_health"
DECAY_DIR = "governance/policy_decay"
DEMOTION_LOG = "governance/policy_demotions.json"

os.makedirs(HEALTH_DIR, exist_ok=True)
os.makedirs(DECAY_DIR, exist_ok=True)

# ==================================================
# TUNABLE THRESHOLDS
# ==================================================

MIN_HEALTH_SCORE = 0.5
MAX_FALSE_POSITIVES = 1

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
# CORE DEMOTION ENGINE — STEP-65
# ==================================================

def maybe_demote_policy_rule(
    tenant: str,
    rule_id: str,
) -> Optional[dict]:
    """
    STEP-65 — Automatic Canary Demotion

    Triggers when:
    • promoted rule health degrades
    • false positives reappear
    • regression is detected

    Action:
    • demote rule to canary
    • allow narrowing again
    """

    policy_path = os.path.join(POLICY_DIR, f"{tenant}.json")
    health_path = os.path.join(HEALTH_DIR, f"{tenant}__{rule_id}.json")
    decay_path = os.path.join(DECAY_DIR, f"{tenant}__{rule_id}.json")

    if not os.path.exists(policy_path):
        return None

    policy = _load_json(policy_path, {})
    rules = policy.get("rules", [])

    health = _load_json(health_path, {})
    decay = _load_json(decay_path, {})

    health_score = health.get("health_score", 1.0)
    false_positives = decay.get("false_positives", 0)

    # --------------------------------------------------
    # DEMOTION CONDITIONS
    # --------------------------------------------------

    if health_score >= MIN_HEALTH_SCORE and false_positives <= MAX_FALSE_POSITIVES:
        return None

    now = datetime.utcnow().isoformat()

    for rule in rules:
        if rule.get("id") != rule_id:
            continue

        # Must have been promoted previously
        if not rule.get("promoted_to_active_at"):
            return None

        # Idempotency
        if rule.get("demoted_at"):
            return rule

        # --------------------------------------------------
        # DEMOTE TO CANARY
        # --------------------------------------------------

        rule["rewidening_mode"] = "canary"
        rule["demoted_at"] = now
        rule.pop("promoted_to_active_at", None)

        # Allow narrowing again
        rule["narrowed"] = False

        policy["last_updated"] = now
        _save_json(policy_path, policy)

        # --------------------------------------------------
        # RESET DECAY SAFELY
        # --------------------------------------------------

        decay["false_positives"] = 0
        decay["clean_events"] = 0
        decay["last_updated"] = now
        _save_json(decay_path, decay)

        # --------------------------------------------------
        # LOG DEMOTION
        # --------------------------------------------------

        log = _load_json(DEMOTION_LOG, [])
        log.append({
            "tenant": tenant,
            "rule_id": rule_id,
            "action": "demoted_to_canary",
            "health_score": health_score,
            "false_positives": false_positives,
            "timestamp": now,
        })
        _save_json(DEMOTION_LOG, log)

        return rule

    return None