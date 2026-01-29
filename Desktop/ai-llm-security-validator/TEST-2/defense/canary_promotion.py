# defense/canary_promotion.py

import os
import json
from datetime import datetime

from defense.metrics_store import snapshot
from defense.canary_health_gate import is_gate_open
from defense.canary_isolation import isolate_canary
from defense.canary_cooldown import start_cooldown

BASE_DIR = "governance/canary_promotion"
os.makedirs(BASE_DIR, exist_ok=True)

# ==================================================
# CONFIG
# ==================================================

PROMOTION_STEPS = [5, 25, 50, 100]

MAX_BLOCK_RATE = 10.0
MAX_AVG_RISK = 0.6

# ==================================================
# FILE HELPERS
# ==================================================

def _path(tenant: str) -> str:
    return os.path.join(BASE_DIR, f"{tenant}.json")


def _load(tenant: str) -> dict:
    if not os.path.exists(_path(tenant)):
        return {
            "tenant": tenant,
            "percentage": 0,
            "status": "idle",
            "started_at": None,
            "last_step_at": None,
        }
    with open(_path(tenant)) as f:
        return json.load(f)


def _save(tenant: str, data: dict):
    with open(_path(tenant), "w") as f:
        json.dump(data, f, indent=2)

# ==================================================
# PROMOTION CONTROLLER
# ==================================================

def advance_promotion(tenant: str) -> dict:
    state = _load(tenant)

    # --------------------------------------------------
    # HEALTH GATE
    # --------------------------------------------------

    if not is_gate_open(tenant):
        return {
            "status": "blocked",
            "reason": "health_gate_closed",
            "state": state,
        }

    metrics = snapshot().get("windowed", {}).get("canary")
    if not metrics:
        return {
            "status": "no_metrics",
            "state": state,
        }

    # --------------------------------------------------
    # REGRESSION GUARD
    # --------------------------------------------------

    if (
        metrics.get("block_rate", 100) > MAX_BLOCK_RATE
        or metrics.get("avg_risk", 1.0) > MAX_AVG_RISK
    ):
        isolate_canary(
            tenant=tenant,
            reason="promotion_regression",
            metrics=metrics,
        )

        start_cooldown(tenant)

        state["status"] = "aborted"
        _save(tenant, state)

        return {
            "status": "aborted",
            "reason": "regression_detected",
            "metrics": metrics,
            "state": state,
        }

    # --------------------------------------------------
    # ADVANCE PROMOTION
    # --------------------------------------------------

    next_steps = [p for p in PROMOTION_STEPS if p > state["percentage"]]

    if not next_steps:
        state["status"] = "completed"
        _save(tenant, state)
        return {
            "status": "completed",
            "state": state,
        }

    state["percentage"] = next_steps[0]
    state["status"] = "in_progress"

    now = datetime.utcnow().isoformat()
    state["last_step_at"] = now
    if not state["started_at"]:
        state["started_at"] = now

    _save(tenant, state)

    return {
        "status": "advanced",
        "tenant": tenant,
        "percentage": state["percentage"],
        "state": state,
    }

# ==================================================
# STATE ACCESSORS
# ==================================================

def get_promotion_state(tenant: str) -> dict:
    return _load(tenant)

# ==================================================
# RESET (STEP-54 SEAL SUPPORT)
# ==================================================

def reset_promotion(tenant: str):
    """
    Hard reset promotion state after successful canary seal.
    Safe to call multiple times.
    """
    path = _path(tenant)
    if os.path.exists(path):
        os.remove(path)