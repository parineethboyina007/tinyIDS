# defense/policy_memory_engine.py

import os
import json
from datetime import datetime

ARCHIVE_DIR = "governance/policy_archive"
ACTIVE_POLICY_TEMPLATE = "governance/adaptive_policies/{tenant}.json"

os.makedirs(ARCHIVE_DIR, exist_ok=True)

# ==================================================
# HELPERS
# ==================================================

def _archive_path(tenant: str, rule_id: str) -> str:
    return os.path.join(ARCHIVE_DIR, f"{tenant}__{rule_id}.json")


def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            content = f.read().strip()
            return json.loads(content) if content else default
    except Exception:
        return default


def _save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ==================================================
# STEP-71 — MEMORY ARCHIVE
# ==================================================

def archive_retired_rule(tenant: str, rule: dict, reason: str):
    """
    Archive rule exactly once for possible resurrection.
    """
    rule_id = rule.get("id")
    if not rule_id:
        return

    path = _archive_path(tenant, rule_id)
    if os.path.exists(path):
        return  # idempotent

    archive = {
        "tenant": tenant,
        "rule": rule,
        "reason": reason,
        "archived_at": datetime.utcnow().isoformat(),
    }

    _save_json(path, archive)


def resurrect_rule_if_needed(
    tenant: str,
    rule_id: str,
    *,
    confidence: float,
    entropy: float,
    threshold: float = 0.6,
):
    """
    STEP-71 — Controlled resurrection

    Conditions:
    • confidence >= threshold
    • entropy <= 0.4
    • rule exists in archive
    • rule not already active
    """

    if confidence < threshold or entropy > 0.4:
        return None

    archive = _load_json(_archive_path(tenant, rule_id), None)
    if not archive:
        return None

    policy_path = ACTIVE_POLICY_TEMPLATE.format(tenant=tenant)
    policy = _load_json(policy_path, None)
    if not policy:
        return None

    # Prevent duplication
    if any(r.get("id") == rule_id for r in policy.get("rules", [])):
        return None

    rule = archive["rule"].copy()

    # Clean retirement flags
    rule.pop("retired", None)
    rule.pop("retired_at", None)
    rule.pop("retired_reason", None)

    rule.update({
        "narrowed": True,
        "resurrected_at": datetime.utcnow().isoformat(),
        "resurrection_reason": "confidence_recovered",
    })

    rule.setdefault("lineage", {}).setdefault("lifecycle", []).append("resurrected")

    policy.setdefault("rules", []).append(rule)
    policy["last_updated"] = datetime.utcnow().isoformat()

    _save_json(policy_path, policy)
    return rule