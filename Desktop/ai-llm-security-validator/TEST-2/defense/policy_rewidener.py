# defense/policy_rewidener.py

import os
import json
from datetime import datetime
from typing import Optional

# ==================================================
# PATHS
# ==================================================

POLICY_DIR = "governance/adaptive_policies"
DECAY_DIR = "governance/policy_decay"
REWIDEN_LOG = "governance/policy_soft_rollbacks.json"

os.makedirs(POLICY_DIR, exist_ok=True)
os.makedirs(DECAY_DIR, exist_ok=True)

# ==================================================
# TUNABLE PARAMETERS
# ==================================================

CLEAN_EVENT_THRESHOLD = 10   # sustained clean traffic before re-widening

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
# CORE RE-WIDENER — STEP-62
# ==================================================

def maybe_rewiden_policy_rule(
    tenant: str,
    rule_id: str,
    policy_mode: str = "active",
) -> Optional[dict]:
    """
    STEP-62 — Canary-only policy re-widening

    Guarantees:
    • rule must be narrowed
    • zero false positives since narrowing
    • sustained clean traffic
    • re-widening happens ONLY in canary
    • idempotent
    • promotion handled later (Step-63)
    """

    # --------------------------------------------------
    # HARD SAFETY: ONLY CANARY MAY RE-WIDEN
    # --------------------------------------------------

    if policy_mode != "canary":
        return None

    policy_path = os.path.join(POLICY_DIR, f"{tenant}.json")
    decay_path = os.path.join(DECAY_DIR, f"{tenant}__{rule_id}.json")

    if not os.path.exists(policy_path):
        return None

    policy = _load_json(policy_path, {})
    rules = policy.get("rules", [])

    decay = _load_json(decay_path, {})
    false_positives = decay.get("false_positives", 0)
    clean_events = decay.get("clean_events", 0)

    # --------------------------------------------------
    # GATING CONDITIONS
    # --------------------------------------------------

    if false_positives > 0:
        return None

    if clean_events < CLEAN_EVENT_THRESHOLD:
        return None

    now = datetime.utcnow().isoformat()

    for rule in rules:
        if rule.get("id") != rule_id:
            continue

        # Must be previously narrowed
        if not rule.get("narrowed"):
            return None

        # Idempotency: already in canary re-widen mode
        if rule.get("rewidening_mode") == "canary":
            return rule

        # --------------------------------------------------
        # APPLY CANARY RE-WIDEN
        # --------------------------------------------------

        rule["severity"] = "Critical"
        rule["rewidening_mode"] = "canary"
        rule["rewidened_at"] = now

        # Explicit observation tracking
        rule["canary_observed"] = False
        rule["canary_clean_events"] = 0

        policy["last_updated"] = now
        _save_json(policy_path, policy)

        # --------------------------------------------------
        # AUDIT LOG (SOFT RE-WIDEN)
        # --------------------------------------------------

        log = _load_json(REWIDEN_LOG, [])
        log.append({
            "tenant": tenant,
            "rule_id": rule_id,
            "action": "rewidened",
            "mode": "canary",
            "reason": "sustained_clean_traffic",
            "timestamp": now,
        })
        _save_json(REWIDEN_LOG, log)

        return rule

    return None