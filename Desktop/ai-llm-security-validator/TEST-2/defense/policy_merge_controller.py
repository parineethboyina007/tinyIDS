# defense/policy_merge_controller.py

import os
import json
from datetime import datetime

CONFIDENCE_DIR = "governance/policy_confidence"
PATCH_DIR = "governance/policy_patches"
ADAPTIVE_DIR = "governance/adaptive_policies"

os.makedirs(ADAPTIVE_DIR, exist_ok=True)

MIN_CONFIDENCE = 3  # 🔐 configurable safety threshold


def _confidence_path(tenant: str, family: str) -> str:
    return os.path.join(CONFIDENCE_DIR, f"{tenant}__{family}.json")


def _patch_path(tenant: str, family: str) -> str:
    return os.path.join(PATCH_DIR, f"{tenant}__{family}.json")


def _adaptive_path(tenant: str) -> str:
    return os.path.join(ADAPTIVE_DIR, f"{tenant}.json")


def _load_json(path: str) -> dict | None:
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _save_json(path: str, data: dict):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ==================================================
# STEP-57 — MERGE CONTROLLER
# ==================================================

def merge_policy_if_confident(tenant: str, family: str) -> dict:
    """
    Merge a learned policy patch into adaptive policy
    ONLY if confidence threshold is met.
    """

    confidence = _load_json(_confidence_path(tenant, family))
    if not confidence:
        return {
            "status": "no_confidence_data",
            "tenant": tenant,
            "family": family,
        }

    if confidence.get("count", 0) < MIN_CONFIDENCE:
        return {
            "status": "insufficient_confidence",
            "tenant": tenant,
            "family": family,
            "count": confidence.get("count", 0),
            "required": MIN_CONFIDENCE,
        }

    patch = _load_json(_patch_path(tenant, family))
    if not patch:
        return {
            "status": "no_patch_found",
            "tenant": tenant,
            "family": family,
        }

    adaptive = _load_json(_adaptive_path(tenant)) or {
        "tenant": tenant,
        "rules": [],
        "updated_at": None,
    }

    # Prevent duplicate merges
    existing_ids = {r.get("id") for r in adaptive["rules"]}
    new_rules = [r for r in patch.get("rules", []) if r.get("id") not in existing_ids]

    if not new_rules:
        return {
            "status": "already_merged",
            "tenant": tenant,
            "family": family,
        }

    adaptive["rules"].extend(new_rules)
    adaptive["updated_at"] = datetime.utcnow().isoformat()

    _save_json(_adaptive_path(tenant), adaptive)

    # Reset confidence AFTER successful merge
    os.remove(_confidence_path(tenant, family))

    return {
        "status": "merged",
        "tenant": tenant,
        "family": family,
        "rules_added": len(new_rules),
        "adaptive_policy_path": _adaptive_path(tenant),
    }