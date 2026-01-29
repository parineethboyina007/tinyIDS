# defense/canary_health_gate.py

import os
import json
from datetime import datetime

from defense.metrics_store import snapshot

BASE_DIR = "governance/canary_health"
os.makedirs(BASE_DIR, exist_ok=True)

# ==========================
# CONFIG (POLICY)
# ==========================

REQUIRED_CLEAN_WINDOWS = 3
MAX_BLOCK_RATE = 5.0
MAX_AVG_RISK = 0.4
WINDOW_COOLDOWN_MINUTES = 2

# ==========================
# FILE HELPERS
# ==========================

def _path(tenant: str) -> str:
    return os.path.join(BASE_DIR, f"{tenant}.json")


def _default_state(tenant: str) -> dict:
    return {
        "tenant": tenant,
        "clean_windows": 0,
        "status": "gated",
        "last_checked": None,
        "opened_at": None,
    }


def _load(tenant: str) -> dict:
    if not os.path.exists(_path(tenant)):
        return _default_state(tenant)
    with open(_path(tenant)) as f:
        return json.load(f)


def _save(tenant: str, data: dict):
    with open(_path(tenant), "w") as f:
        json.dump(data, f, indent=2)

# ==========================
# CORE LOGIC
# ==========================

def evaluate_health_window(tenant: str) -> dict:
    """
    Evaluate canary health window and advance gate if clean.

    Returns STATE + POLICY metadata (required windows).
    """

    state = _load(tenant)

    # Already open → no further evaluation
    if state["status"] == "open":
        return {
            **state,
            "required": REQUIRED_CLEAN_WINDOWS,
        }

    metrics = snapshot().get("windowed", {}).get("canary")
    if not metrics:
        return {
            **state,
            "required": REQUIRED_CLEAN_WINDOWS,
        }

    clean = (
        metrics.get("block_rate", 100.0) <= MAX_BLOCK_RATE
        and metrics.get("avg_risk", 1.0) <= MAX_AVG_RISK
    )

    now = datetime.utcnow()

    if clean:
        state["clean_windows"] += 1
    else:
        state["clean_windows"] = 0

    state["last_checked"] = now.isoformat()

    if state["clean_windows"] >= REQUIRED_CLEAN_WINDOWS:
        state["status"] = "open"
        state["opened_at"] = now.isoformat()

    _save(tenant, state)

    return {
        **state,
        "required": REQUIRED_CLEAN_WINDOWS,
    }


def is_gate_open(tenant: str) -> bool:
    return _load(tenant).get("status") == "open"


def reset_gate(tenant: str):
    """
    Hard reset gate state (used after incidents or forced rollback).
    """
    if os.path.exists(_path(tenant)):
        os.remove(_path(tenant))