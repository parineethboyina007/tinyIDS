# defense/policy_federated_confidence.py

import os
import json
from datetime import datetime
from typing import Dict

# ==================================================
# PATHS
# ==================================================

FEDERATED_FILE = "governance/federated_confidence.json"
os.makedirs("governance", exist_ok=True)

# ==================================================
# DEFAULT STRUCTURE
# ==================================================

DEFAULT_STATE = {
    "families": {},
    "last_updated": None
}

# ==================================================
# SAFE JSON HELPERS
# ==================================================

def _load_state() -> dict:
    if not os.path.exists(FEDERATED_FILE):
        return DEFAULT_STATE.copy()
    try:
        with open(FEDERATED_FILE) as f:
            content = f.read().strip()
            return json.loads(content) if content else DEFAULT_STATE.copy()
    except Exception:
        return DEFAULT_STATE.copy()


def _save_state(state: dict):
    with open(FEDERATED_FILE, "w") as f:
        json.dump(state, f, indent=2)


# ==================================================
# CORE ENGINE — STEP-66
# ==================================================

def publish_confidence_signal(
    tenant: str,
    family: str,
    outcome: str,
):
    """
    Tenant publishes a confidence signal.

    outcome ∈ {"effective", "false_positive"}
    """

    state = _load_state()
    families = state.setdefault("families", {})

    fam = families.setdefault(family, {
        "effective": 0,
        "false_positive": 0,
        "contributors": {},
        "confidence": 0.5,
    })

    # Track per-tenant contribution count (NOT traffic)
    fam["contributors"].setdefault(tenant, 0)
    fam["contributors"][tenant] += 1

    if outcome == "effective":
        fam["effective"] += 1
    elif outcome == "false_positive":
        fam["false_positive"] += 1
    else:
        return

    # --------------------------------------------------
    # CONFIDENCE CALCULATION
    # --------------------------------------------------

    total = fam["effective"] + fam["false_positive"]
    if total > 0:
        fam["confidence"] = round(fam["effective"] / total, 3)

    state["last_updated"] = datetime.utcnow().isoformat()
    _save_state(state)


def get_family_confidence(family: str) -> Dict:
    """
    Used by policy_evolution_engine for faster decisions.
    """
    state = _load_state()
    return state.get("families", {}).get(family, {
        "confidence": 0.5,
        "effective": 0,
        "false_positive": 0,
        "contributors": {},
    })