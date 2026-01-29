# defense/threshold_rollback_guard.py

from datetime import datetime
from defense.metrics_store import snapshot
from defense.adaptive_thresholds import load_thresholds, save_thresholds

MAX_BLOCK_RATE = 80.0
MAX_DELTA = 30.0
MIN_CANARY_ADVANTAGE = 20.0


def auto_rollback_thresholds():
    metrics = snapshot().get("windowed", {})
    active = metrics.get("active")
    canary = metrics.get("canary")

    if not active:
        return {"status": "no_active_metrics"}

    active_thr = load_thresholds("active")
    canary_thr = load_thresholds("canary")

    reasons = []

    # 1️⃣ Absolute over-blocking
    if active["block_rate"] > MAX_BLOCK_RATE:
        reasons.append("block_rate_too_high")

    # 2️⃣ Sudden spike
    delta = active["block_rate"] - canary.get("block_rate", 0)
    if delta > MAX_DELTA:
        reasons.append("sudden_block_rate_spike")

    # 3️⃣ Canary significantly safer
    if canary and (canary["block_rate"] + MIN_CANARY_ADVANTAGE) < active["block_rate"]:
        reasons.append("canary_safer_than_active")

    if not reasons:
        return {
            "status": "stable",
            "active_block_rate": active["block_rate"]
        }

    # 🔁 Roll back ACTIVE → CANARY thresholds
    save_thresholds("active", canary_thr)

    return {
        "status": "rolled_back",
        "timestamp": datetime.utcnow().isoformat(),
        "reasons": reasons,
        "restored_thresholds": canary_thr
    }