# defense/canary_isolation.py

import os
import json
from datetime import datetime
from typing import Optional

# ==================================================
# PATHS
# ==================================================

ISOLATION_DIR = "governance/canary_isolation"
os.makedirs(ISOLATION_DIR, exist_ok=True)

# ==================================================
# HELPERS
# ==================================================

def _path(tenant: str) -> str:
    return os.path.join(ISOLATION_DIR, f"{tenant}.json")

# ==================================================
# CORE API
# ==================================================

def isolate_canary(tenant: str, reason: str, metrics: dict) -> dict:
    """
    Hard-isolate a canary due to terminal failure conditions.
    This is a one-way action until explicitly cleared.
    """

    record = {
        "tenant": tenant,
        "isolated_at": datetime.utcnow().isoformat(),
        "reason": reason,
        "metrics": metrics,
        "status": "isolated",
    }

    with open(_path(tenant), "w") as f:
        json.dump(record, f, indent=2)

    return record


def is_canary_isolated(tenant: str) -> bool:
    """
    Returns True only if canary is actively isolated.
    Cleared isolations do not count.
    """
    record = load_isolation(tenant)
    return bool(record and record.get("status") == "isolated")


def load_isolation(tenant: str) -> Optional[dict]:
    """
    Load isolation record if it exists.
    """
    path = _path(tenant)
    if not os.path.exists(path):
        return None

    with open(path) as f:
        return json.load(f)


def clear_isolation(tenant: str, reason: str) -> dict:
    """
    Clear an active canary isolation after human review.
    Does NOT delete the record (audit preserved).
    """

    record = load_isolation(tenant)
    if not record:
        return {"status": "not_isolated"}

    if record.get("status") != "isolated":
        return {
            "status": "already_cleared",
            "tenant": tenant,
        }

    record["cleared_at"] = datetime.utcnow().isoformat()
    record["clear_reason"] = reason
    record["status"] = "cleared"

    with open(_path(tenant), "w") as f:
        json.dump(record, f, indent=2)

    return record

# ==================================================
# SAFETY GUARDS
# ==================================================

def isolation_summary(tenant: str) -> dict:
    """
    Lightweight status view for APIs / dashboards.
    """
    record = load_isolation(tenant)
    if not record:
        return {
            "tenant": tenant,
            "isolated": False,
        }

    return {
        "tenant": tenant,
        "isolated": record.get("status") == "isolated",
        "status": record.get("status"),
        "reason": record.get("reason"),
        "isolated_at": record.get("isolated_at"),
        "cleared_at": record.get("cleared_at"),
    }