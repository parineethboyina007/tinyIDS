# defense/policy_drift_responder.py

from datetime import datetime

from defense.policy_narrower import narrow_policy_rule
from defense.policy_demoter import maybe_demote_policy_rule
from defense.policy_rewidener import maybe_rewiden_policy_rule

# ==================================================
# DRIFT THRESHOLDS — STEP-68
# ==================================================

DRIFT_LOW = 0.15
DRIFT_MEDIUM = 0.35
DRIFT_HIGH = 0.60

# ==================================================
# CORE RESPONDER
# ==================================================

def respond_to_policy_drift(
    tenant: str,
    rule_id: str,
    drift_score: float,
    false_positives: int,
    health_score: float | None = None,
):
    """
    STEP-68 — Drift-Driven Auto-Actions

    Conservative, reversible, health-aware.
    """

    now = datetime.utcnow().isoformat()

    # ----------------------------------------------
    # EXTREME DRIFT → OBSERVE ONLY
    # ----------------------------------------------
    if drift_score >= DRIFT_HIGH:
        return {
            "action": "observe_only",
            "reason": "extreme_drift_requires_human_review",
            "rule_id": rule_id,
            "drift": drift_score,
            "timestamp": now,
        }

    # ----------------------------------------------
    # MEDIUM DRIFT + FALSE POSITIVES → NARROW
    # ----------------------------------------------
    if drift_score >= DRIFT_MEDIUM and false_positives > 0:
        rule = narrow_policy_rule(
            tenant=tenant,
            rule_id=rule_id,
            reason="drift_and_false_positives",
        )
        if rule:
            return {
                "action": "narrowed",
                "rule_id": rule_id,
                "drift": drift_score,
                "timestamp": now,
            }

    # ----------------------------------------------
    # MEDIUM DRIFT + LOW HEALTH → DEMOTE
    # ----------------------------------------------
    if drift_score >= DRIFT_MEDIUM and health_score is not None:
        if health_score < 0.5:
            rule = maybe_demote_policy_rule(tenant, rule_id)
            if rule:
                return {
                    "action": "demoted",
                    "rule_id": rule_id,
                    "drift": drift_score,
                    "health": health_score,
                    "timestamp": now,
                }

    # ----------------------------------------------
    # LOW DRIFT → POSSIBLE RE-WIDEN
    # ----------------------------------------------
    if drift_score <= DRIFT_LOW:
        rule = maybe_rewiden_policy_rule(tenant, rule_id)
        if rule:
            return {
                "action": "rewidened",
                "rule_id": rule_id,
                "drift": drift_score,
                "timestamp": now,
            }

    return {
        "action": "no_action",
        "rule_id": rule_id,
        "drift": drift_score,
        "timestamp": now,
    }