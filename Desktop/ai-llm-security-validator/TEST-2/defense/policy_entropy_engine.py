# defense/policy_entropy_engine.py

import os
import json
from datetime import datetime

# ==================================================
# PATHS
# ==================================================

ENTROPY_DIR = "governance/policy_entropy"
os.makedirs(ENTROPY_DIR, exist_ok=True)

# ==================================================
# TUNABLE PARAMETERS
# ==================================================

ENTROPY_DECAY_CLEAN = 0.05
ENTROPY_DECAY_BLOCK = 0.02
ENTROPY_INCREASE_FP = 0.25

ENTROPY_SOFT_LIMIT = 0.4
ENTROPY_HARD_LIMIT = 0.8

MIN_ENTROPY = 0.0
MAX_ENTROPY = 1.0

# ==================================================
# HELPERS
# ==================================================

def _entropy_path(tenant: str, rule_id: str) -> str:
    return os.path.join(ENTROPY_DIR, f"{tenant}__{rule_id}.json")


def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            return json.loads(f.read().strip() or "{}")
    except Exception:
        return default


def _save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# ==================================================
# STEP-69 — ENTROPY ENGINE
# ==================================================

def update_policy_entropy(
    tenant: str,
    rule_id: str,
    *,
    blocked: bool,
    false_positive: bool = False,
) -> dict:

    now = datetime.utcnow().isoformat()
    path = _entropy_path(tenant, rule_id)

    state = _load_json(path, {
        "tenant": tenant,
        "rule_id": rule_id,
        "entropy": 0.0,
        "last_updated": None,
    })

    entropy = float(state.get("entropy", 0.0))

    if false_positive:
        entropy += ENTROPY_INCREASE_FP
    elif blocked:
        entropy -= ENTROPY_DECAY_BLOCK
    else:
        entropy -= ENTROPY_DECAY_CLEAN

    entropy = max(MIN_ENTROPY, min(MAX_ENTROPY, entropy))

    state.update({
        "entropy": entropy,
        "last_updated": now,
    })

    _save_json(path, state)
    return state


def entropy_action(entropy: float) -> str:
    if entropy >= ENTROPY_HARD_LIMIT:
        return "retire"
    if entropy >= ENTROPY_SOFT_LIMIT:
        return "narrow"
    return "stable"