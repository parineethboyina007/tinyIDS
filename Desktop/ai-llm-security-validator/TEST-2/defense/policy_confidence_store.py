# defense/policy_confidence_store.py

import os
import json
from datetime import datetime

CONFIDENCE_DIR = "governance/policy_confidence"
MIN_CONFIDENCE_TO_COMMIT = 5

os.makedirs(CONFIDENCE_DIR, exist_ok=True)


def _path(tenant: str, family: str) -> str:
    return os.path.join(CONFIDENCE_DIR, f"{tenant}__{family}.json")


def record_signal(tenant: str, family: str) -> dict:
    """
    Record an attack-family signal.
    Crash-safe, idempotent, filesystem-safe.
    """

    os.makedirs(CONFIDENCE_DIR, exist_ok=True)
    path = _path(tenant, family)
    now = datetime.utcnow().isoformat()

    if os.path.exists(path):
        with open(path) as f:
            state = json.load(f)
    else:
        state = {
            "tenant": tenant,
            "family": family,
            "count": 0,
            "first_seen": now,
            "last_seen": now,
        }

    state["count"] += 1
    state["last_seen"] = now

    with open(path, "w") as f:
        json.dump(state, f, indent=2)

    return state


def is_confident_enough(tenant: str, family: str) -> bool:
    """
    Returns True if confidence threshold is met.
    Safe even if state file does not exist.
    """

    path = _path(tenant, family)
    if not os.path.exists(path):
        return False

    with open(path) as f:
        state = json.load(f)

    return state.get("count", 0) >= MIN_CONFIDENCE_TO_COMMIT


def get_confidence(tenant: str, family: str) -> dict:
    """
    Read-only access to confidence state.
    Used by guards, APIs, and explainability.
    """

    path = _path(tenant, family)
    if not os.path.exists(path):
        return {
            "tenant": tenant,
            "family": family,
            "count": 0,
            "first_seen": None,
            "last_seen": None,
            "confident": False,
        }

    with open(path) as f:
        state = json.load(f)

    state["confident"] = state.get("count", 0) >= MIN_CONFIDENCE_TO_COMMIT
    return state