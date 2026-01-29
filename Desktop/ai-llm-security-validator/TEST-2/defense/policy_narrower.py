# defense/policy_narrower.py

import os
import json
from datetime import datetime
from typing import Dict, Optional

# ==================================================
# PATHS
# ==================================================

POLICY_DIR = "governance/adaptive_policies"
MUTATION_LOG = "governance/policy_soft_rollbacks.json"

os.makedirs(POLICY_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MUTATION_LOG), exist_ok=True)

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


def _log_mutation(entry: Dict):
    mutations = _load_json(MUTATION_LOG, [])
    mutations.append(entry)
    _save_json(MUTATION_LOG, mutations)

# ==================================================
# POLICY NARROWING ENGINE (STEP-59B)
# ==================================================

def narrow_policy_rule(
    tenant: str,
    rule_id: str,
    reason: str = "false_positive_detected",
) -> Optional[Dict]:
    """
    STEP-59B — Policy Narrowing (not deletion)

    This function:
    • reduces blast radius
    • preserves learned intent
    • avoids hard rollback
    • is fully auditable
    • is idempotent
    """

    policy_path = os.path.join(POLICY_DIR, f"{tenant}.json")

    if not os.path.exists(policy_path):
        return None

    policy = _load_json(policy_path, {})
    rules = policy.get("rules", [])

    now = datetime.utcnow().isoformat()
    updated_rule = None

    for rule in rules:
        if rule.get("id") != rule_id:
            continue

        # -----------------------------
        # IDEMPOTENCY GUARD
        # -----------------------------
        if rule.get("narrowed"):
            return rule

        # -----------------------------
        # NARROWING STRATEGY
        # -----------------------------

        rule["severity"] = "High"  # downgrade from Critical
        rule["narrowed"] = True
        rule["narrowed_at"] = now

        # Require explicit malicious intent verbs
        rule["require_context"] = [
            "write",
            "create",
            "build",
            "generate",
        ]

        updated_rule = rule

        # -----------------------------
        # AUDIT LOG
        # -----------------------------

        _log_mutation({
            "tenant": tenant,
            "rule_id": rule_id,
            "action": "narrowed",
            "reason": reason,
            "timestamp": now,
        })

        break

    if not updated_rule:
        return None

    policy["last_updated"] = now
    _save_json(policy_path, policy)

    return updated_rule