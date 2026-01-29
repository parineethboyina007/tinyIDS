# defense/threshold_saturation_detector.py

from defense.metrics_store import snapshot
from defense.threshold_version_store import list_versions, load_version
from defense.adaptive_thresholds import load_thresholds, save_thresholds
from defense.threshold_version_store import create_version
from datetime import datetime

SATURATION_BLOCK_RATE = 80
SATURATION_RISK = 0.9
MIN_RISK_THRESHOLD = 0.6
MAX_SEVERITY = "Critical"
REQUIRED_WINDOWS = 3


def detect_saturation(tenant: str, mode: str = "canary") -> bool:
    metrics = snapshot().get("windowed", {}).get(mode)
    if not metrics:
        return False

    thresholds = load_thresholds(mode, tenant)

    return (
        metrics.get("block_rate", 0) > SATURATION_BLOCK_RATE
        and metrics.get("avg_risk", 0) > SATURATION_RISK
        and thresholds["severity_floor"] == MAX_SEVERITY
        and thresholds["risk_block_threshold"] <= MIN_RISK_THRESHOLD
    )


def select_rollback_candidate(tenant: str, mode: str):
    versions = list_versions(tenant, mode)

    # Walk backwards and find a less restrictive version
    for v in reversed(versions):
        snap = load_version(tenant, mode, v["version"])
        t = snap["thresholds"]

        if (
            t["severity_floor"] != MAX_SEVERITY
            or t["risk_block_threshold"] > MIN_RISK_THRESHOLD
        ):
            return snap

    return None


def execute_auto_rollback(tenant: str, mode: str):
    candidate = select_rollback_candidate(tenant, mode)
    if not candidate:
        return {"status": "no_safe_rollback"}

    save_thresholds(mode, tenant, candidate["thresholds"])

    create_version(
        tenant=tenant,
        mode=mode,
        thresholds=candidate["thresholds"],
        reason="auto_rollback_saturation",
        parent=candidate["version"],
    )

    return {
        "status": "rolled_back",
        "tenant": tenant,
        "mode": mode,
        "rolled_back_to": candidate["version"],
        "thresholds": candidate["thresholds"],
        "timestamp": datetime.utcnow().isoformat(),
    }