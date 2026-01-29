# defense/auto_rollback.py

import uuid
from datetime import datetime

from defense.metrics_store import snapshot
from defense.policy_store import rollback_to_last_safe
from audit.promotion_store import save_rollback_report

# ==================================================
# AUTO ROLLBACK THRESHOLDS
# ==================================================

MAX_ACTIVE_BLOCK_RATE = 90.0
MAX_ACTIVE_AVG_RISK = 0.9
MIN_REQUESTS = 20


def auto_rollback_if_unsafe():
    rollback_id = str(uuid.uuid4())
    metrics = snapshot()
    windowed = metrics.get("windowed", {})

    # --------------------------------------------------
    # METRICS PRESENCE
    # --------------------------------------------------
    if "active" not in windowed:
        return {
            "status": "no_active_metrics"
        }

    active = windowed["active"]

    if active["requests"] < MIN_REQUESTS:
        return {
            "status": "insufficient_data",
            "active_requests": active["requests"]
        }

    unsafe = (
        active["block_rate"] >= MAX_ACTIVE_BLOCK_RATE or
        active["avg_risk"] >= MAX_ACTIVE_AVG_RISK
    )

    if not unsafe:
        return {
            "status": "stable",
            "active_policy_safe": True
        }

    # --------------------------------------------------
    # ATTEMPT ROLLBACK
    # --------------------------------------------------
    try:
        rolled_back_to = rollback_to_last_safe()
    except RuntimeError:
        report = {
            "rollback_id": rollback_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "no_last_safe_policy",
            "metrics": active,
            "action": "manual_intervention_required"
        }

        save_rollback_report(report)
        return report

    # --------------------------------------------------
    # SUCCESSFUL ROLLBACK
    # --------------------------------------------------
    report = {
        "rollback_id": rollback_id,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "rolled_back",
        "rolled_back_to": rolled_back_to,
        "metrics": active
    }

    save_rollback_report(report)
    return report