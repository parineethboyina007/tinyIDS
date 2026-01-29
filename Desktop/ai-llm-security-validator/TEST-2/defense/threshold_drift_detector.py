# defense/threshold_drift_detector.py

from datetime import datetime, timedelta
from defense.threshold_version_store import list_versions, load_version
from defense.threshold_freeze_guard import freeze_thresholds

MAX_RISK_DRIFT = 0.15
MAX_SEVERITY_DRIFT = 1
OSCILLATION_WINDOW_MIN = 30
MAX_CHANGES_IN_WINDOW = 3

SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]


def _severity_index(sev: str) -> int:
    return SEVERITY_ORDER.index(sev)


def detect_threshold_drift(tenant: str, mode: str = "active") -> dict:

    versions = list_versions(tenant, mode)
    if len(versions) < 2:
        return {
            "status": "ok",
            "tenant": tenant,
            "mode": mode,
            "message": "Not enough history for drift detection",
        }

    baseline = load_version(tenant, mode, versions[0]["version"])
    latest = load_version(tenant, mode, versions[-1]["version"])

    b = baseline["thresholds"]
    l = latest["thresholds"]

    alerts = []

    # ---------------- RISK DRIFT ----------------

    risk_delta = abs(l["risk_block_threshold"] - b["risk_block_threshold"])
    if risk_delta > MAX_RISK_DRIFT:
        alerts.append({
            "type": "risk_drift",
            "baseline": b["risk_block_threshold"],
            "current": l["risk_block_threshold"],
            "delta": risk_delta,
        })

    # ---------------- SEVERITY DRIFT ----------------

    sev_delta = abs(
        _severity_index(l["severity_floor"]) -
        _severity_index(b["severity_floor"])
    )

    if sev_delta > MAX_SEVERITY_DRIFT:
        alerts.append({
            "type": "severity_drift",
            "baseline": b["severity_floor"],
            "current": l["severity_floor"],
            "levels": sev_delta,
        })

    # ---------------- OSCILLATION ----------------

    now = datetime.utcnow()
    recent = [
        v for v in versions
        if now - datetime.fromisoformat(v["created_at"])
        <= timedelta(minutes=OSCILLATION_WINDOW_MIN)
    ]

    if len(recent) > MAX_CHANGES_IN_WINDOW:
        alerts.append({
            "type": "oscillation",
            "changes": len(recent),
            "window_minutes": OSCILLATION_WINDOW_MIN,
        })

    # ---------------- AUTO FREEZE ----------------

    if alerts:
        scope = {}

        for alert in alerts:
            if alert["type"] == "severity_drift":
                scope["severity_floor"] = True
            if alert["type"] == "risk_drift":
                scope["risk_block_threshold"] = True
            if alert["type"] == "oscillation":
                scope = {
                    "severity_floor": True,
                    "risk_block_threshold": True,
                }

        freeze_thresholds(
            tenant=tenant,
            reason="threshold_drift",
            scope=scope,
        )

        return {
            "status": "alert",
            "tenant": tenant,
            "mode": mode,
            "alerts": alerts,
        }

    return {
        "status": "ok",
        "tenant": tenant,
        "mode": mode,
        "message": "No threshold drift detected",
    }