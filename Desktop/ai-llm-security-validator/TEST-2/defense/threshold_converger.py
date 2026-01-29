# defense/threshold_converger.py

from datetime import datetime, timedelta
from fastapi import HTTPException

from defense.adaptive_thresholds import (
    load_thresholds,
    save_thresholds,
)
from defense.metrics_store import snapshot

# ==============================
# CONFIG
# ==============================

MIN_STABLE_MINUTES = 5
MAX_BLOCK_RATE_DELTA = 5.0   # %
MAX_RISK_DELTA = 0.1

# ==============================
# HELPERS
# ==============================

def _parse_time(ts: str):
    return datetime.fromisoformat(ts)


# ==============================
# CORE ENGINE
# ==============================

def auto_converge_thresholds():
    """
    Automatically converge canary thresholds into active
    if canary proves stable and safe.
    """

    canary = load_thresholds("canary")
    active = load_thresholds("active")

    # ----------------------------------
    # GUARD 1 — Canary must be adapted
    # ----------------------------------
    if not canary.get("last_updated"):
        raise HTTPException(
            409,
            "Cannot converge: canary thresholds were never adapted"
        )

    # ----------------------------------
    # GUARD 2 — Stability window
    # ----------------------------------
    last_update = _parse_time(canary["last_updated"])
    if datetime.utcnow() - last_update < timedelta(minutes=MIN_STABLE_MINUTES):
        return {
            "status": "waiting",
            "reason": "stability_window_not_met",
            "stable_minutes": (
                datetime.utcnow() - last_update
            ).seconds // 60
        }

    # ----------------------------------
    # GUARD 3 — Metrics safety
    # ----------------------------------
    metrics = snapshot().get("windowed", {})

    if "canary" not in metrics or "active" not in metrics:
        return {
            "status": "waiting",
            "reason": "missing_metrics"
        }

    canary_m = metrics["canary"]
    active_m = metrics["active"]

    block_rate_delta = canary_m["block_rate"] - active_m["block_rate"]
    risk_delta = canary_m["avg_risk"] - active_m["avg_risk"]

    if block_rate_delta > MAX_BLOCK_RATE_DELTA:
        return {
            "status": "blocked",
            "reason": "block_rate_regression",
            "delta": block_rate_delta
        }

    if risk_delta > MAX_RISK_DELTA:
        return {
            "status": "blocked",
            "reason": "risk_regression",
            "delta": risk_delta
        }

    # ----------------------------------
    # CONVERGE
    # ----------------------------------
    save_thresholds("active", canary)

    return {
        "status": "converged",
        "source": "canary",
        "target": "active",
        "thresholds": canary
    }