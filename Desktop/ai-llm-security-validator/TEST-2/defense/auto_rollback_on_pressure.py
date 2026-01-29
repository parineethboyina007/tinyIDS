# defense/auto_rollback_on_pressure.py

from datetime import datetime
from defense.metrics_store import snapshot
from defense.threshold_version_store import (
    list_versions,
    load_version,
    create_version,
)
from defense.adaptive_thresholds import load_thresholds, save_thresholds
from defense.threshold_freeze_guard import freeze_thresholds

# ==================================================
# CONFIG
# ==================================================

MAX_BLOCK_RATE = 65.0
MIN_WINDOWS = 3
MAXED_RISK = 0.6
MAXED_SEVERITY = "Critical"

# ==================================================
# HELPERS
# ==================================================

def _is_maxed(thresholds: dict) -> bool:
    return (
        thresholds.get("risk_block_threshold") <= MAXED_RISK
        and thresholds.get("severity_floor") == MAXED_SEVERITY
    )

def _last_safe_version(tenant: str):
    versions = list_versions(tenant, "canary")
    for v in reversed(versions):
        snap = load_version(tenant, "canary", v["version"])
        if snap["thresholds"]["severity_floor"] != MAXED_SEVERITY:
            return snap
    return None

# ==================================================
# AUTO ROLLBACK CONTROLLER (STEP-39)
# ==================================================

def auto_rollback_on_pressure(tenant: str = "default") -> dict:

    metrics = snapshot().get("windowed", {}).get("canary")
    if not metrics:
        return {"status": "no_metrics"}

    block_rate = metrics.get("block_rate", 0)

    thresholds = load_thresholds("canary", tenant)

    if block_rate < MAX_BLOCK_RATE:
        return {"status": "pressure_ok"}

    if not _is_maxed(thresholds):
        return {"status": "not_maxed"}

    versions = list_versions(tenant, "canary")
    if len(versions) < MIN_WINDOWS:
        return {"status": "insufficient_history"}

    safe = _last_safe_version(tenant)
    if not safe:
        return {"status": "no_safe_version"}

    # ---------------- ROLLBACK ----------------

    save_thresholds("canary", tenant, safe["thresholds"])

    create_version(
        tenant=tenant,
        mode="canary",
        thresholds=safe["thresholds"],
        reason="auto_rollback_on_pressure",
        parent=versions[-1]["version"],
    )

    # ---------------- FREEZE ----------------

    freeze_thresholds(
        tenant=tenant,
        reason="sustained_attack_pressure",
        cooldown_minutes=30,
        scope={
            "severity_floor": True,
            "risk_block_threshold": True,
        },
    )

    return {
        "status": "rolled_back",
        "tenant": tenant,
        "rolled_to_version": safe["version"],
        "block_rate": block_rate,
        "timestamp": datetime.utcnow().isoformat(),
    }