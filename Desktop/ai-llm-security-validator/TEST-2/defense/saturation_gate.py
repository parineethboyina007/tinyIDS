# defense/saturation_gate.py

from datetime import datetime, timedelta

# ==================================================
# SATURATION GATE CONFIG
# ==================================================

SATURATION_BLOCK_RATE = 90.0
SATURATION_AVG_RISK = 0.95
SATURATION_SEVERITY = "Critical"

# Minimum time between adaptations before escalation (minutes)
ESCALATION_COOLDOWN_MINUTES = 5


# ==================================================
# GATE CHECK
# ==================================================

def is_escalated(
    metrics: dict,
    thresholds: dict,
    last_updated: str | None,
) -> dict:
    """
    Determines whether the system must STOP adapting
    and allow rollback-only behavior.
    """

    if not metrics or not thresholds:
        return {"escalated": False}

    block_rate = metrics.get("block_rate", 0)
    avg_risk = metrics.get("avg_risk", 0)
    severity = thresholds.get("severity_floor")

    if (
        block_rate < SATURATION_BLOCK_RATE
        or avg_risk < SATURATION_AVG_RISK
        or severity != SATURATION_SEVERITY
    ):
        return {"escalated": False}

    if not last_updated:
        return {"escalated": False}

    last = datetime.fromisoformat(last_updated)
    delta = datetime.utcnow() - last

    if delta < timedelta(minutes=ESCALATION_COOLDOWN_MINUTES):
        return {
            "escalated": True,
            "reason": "repeated_adaptation_under_saturation",
            "cooldown_minutes": ESCALATION_COOLDOWN_MINUTES,
        }

    return {
        "escalated": True,
        "reason": "terminal_saturation",
    }