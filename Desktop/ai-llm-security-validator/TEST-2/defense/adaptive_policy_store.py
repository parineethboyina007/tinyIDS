# defense/adaptive_policy_store.py

import os
import json
from datetime import datetime
from typing import Dict

CONFIDENCE_DIR = "governance/policy_confidence"
POLICY_DIR = "governance/adaptive_policies"

os.makedirs(CONFIDENCE_DIR, exist_ok=True)
os.makedirs(POLICY_DIR, exist_ok=True)

MIN_CONFIDENCE_TO_COMMIT = 5


# ==================================================
# PATH HELPERS
# ==================================================

def _confidence_path(tenant: str, family: str) -> str:
    return os.path.join(CONFIDENCE_DIR, f"{tenant}__{family}.json")


def _policy_path(tenant: str) -> str:
    return os.path.join(POLICY_DIR, f"{tenant}.json")


# ==================================================
# CONFIDENCE TRACKING
# ==================================================

def _load_confidence(tenant: str, family: str) -> Dict:
    path = _confidence_path(tenant, family)
    if not os.path.exists(path):
        return {
            "tenant": tenant,
            "family": family,
            "count": 0,
            "first_seen": None,
            "last_seen": None,
        }
    with open(path) as f:
        return json.load(f)


def _save_confidence(data: Dict):
    with open(_confidence_path(data["tenant"], data["family"]), "w") as f:
        json.dump(data, f, indent=2)


# ==================================================
# ADAPTIVE POLICY STORE
# ==================================================

def save_policy_patch(tenant: str, family: str, patch: Dict) -> Dict:
    """
    STEP-57 — Confidence-gated adaptive policy persistence

    • Tracks repeated attack families
    • Commits only after confidence threshold
    • De-duplicates rules by ID
    • Produces enforceable adaptive policy file
    """

    now = datetime.utcnow().isoformat()

    # --------------------------------------------------
    # UPDATE CONFIDENCE
    # --------------------------------------------------

    confidence = _load_confidence(tenant, family)
    confidence["count"] += 1
    confidence["last_seen"] = now
    if not confidence["first_seen"]:
        confidence["first_seen"] = now

    _save_confidence(confidence)

    if confidence["count"] < MIN_CONFIDENCE_TO_COMMIT:
        return {
            "status": "deferred",
            "tenant": tenant,
            "family": family,
            "confidence": confidence["count"],
            "required": MIN_CONFIDENCE_TO_COMMIT,
        }

    # --------------------------------------------------
    # LOAD OR INIT POLICY
    # --------------------------------------------------

    policy_path = _policy_path(tenant)

    if os.path.exists(policy_path):
        with open(policy_path) as f:
            policy = json.load(f)
    else:
        policy = {
            "tenant": tenant,
            "generated_at": now,
            "rules": [],
        }

    existing_rule_ids = {
        r["id"]
        for r in policy.get("rules", [])
        if isinstance(r, dict) and "id" in r
    }

    # --------------------------------------------------
    # COMMIT PATCH RULES
    # --------------------------------------------------

    committed = []

    for rule in patch.get("rules", []):
        rule_id = rule.get("id")
        if not rule_id or rule_id in existing_rule_ids:
            continue

        rule_entry = {
            **rule,
            "family": family,
            "confidence": confidence["count"],
            "committed_at": now,
        }

        policy["rules"].append(rule_entry)
        committed.append(rule_id)

    policy["last_updated"] = now

    with open(policy_path, "w") as f:
        json.dump(policy, f, indent=2)

    return {
        "status": "committed",
        "tenant": tenant,
        "family": family,
        "confidence": confidence["count"],
        "committed_rules": committed,
        "policy_path": policy_path,
    }   