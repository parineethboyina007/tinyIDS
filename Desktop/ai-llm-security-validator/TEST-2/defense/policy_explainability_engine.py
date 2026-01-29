# defense/policy_explainability_engine.py

from datetime import datetime

from defense.policy_entropy_engine import entropy_action
from defense.policy_timeline_engine import replay_policy_timeline
from defense.policy_health_engine import evaluate_canary_rule_health
from defense.policy_drift_detector import evaluate_policy_drift


# ==================================================
# STEP-74 — DECISION EXPLAINABILITY GRAPH
# ==================================================

def explain_policy_decision(
    *,
    tenant: str,
    rule_id: str,
    blocked: bool,
    risk: float,
):
    """
    Produce a full causal explanation for a decision:
    WHY blocked / allowed at this moment.
    """

    # ----------------------------
    # Gather signals
    # ----------------------------

    timeline = replay_policy_timeline(tenant, rule_id)

    health = evaluate_canary_rule_health(tenant, rule_id) or {}
    drift = evaluate_policy_drift(
        tenant=tenant,
        rule_id=rule_id,
        blocked=blocked,
        false_positive=False,
    )

    entropy = None
    try:
        from defense.policy_entropy_engine import _entropy_path, _load_json
        path = _entropy_path(tenant, rule_id)
        entropy_state = _load_json(path, {})
        entropy = entropy_state.get("entropy")
    except Exception:
        entropy = None

    entropy_decision = entropy_action(entropy) if entropy is not None else "unknown"

    # ----------------------------
    # Explanation synthesis
    # ----------------------------

    explanation = {
        "tenant": tenant,
        "rule_id": rule_id,
        "decision": "blocked" if blocked else "allowed",
        "risk_score": risk,
        "entropy": entropy,
        "entropy_decision": entropy_decision,
        "drift_score": drift.get("drift_score"),
        "health_score": health.get("health_score"),
        "confidence": health.get("confidence"),
        "timeline_summary": [
            {
                "event": e["event"],
                "timestamp": e.get("timestamp"),
            }
            for e in timeline.get("events", [])
        ],
        "final_reason": _derive_final_reason(
            blocked=blocked,
            entropy_decision=entropy_decision,
            drift_score=drift.get("drift_score", 0.0),
            health_score=health.get("health_score", 1.0),
        ),
        "generated_at": datetime.utcnow().isoformat(),
    }

    return explanation


# ==================================================
# INTERNAL LOGIC
# ==================================================

def _derive_final_reason(*, blocked, entropy_decision, drift_score, health_score):
    if blocked:
        if entropy_decision == "retire":
            return "Rule blocked due to excessive entropy (false positives)"
        if drift_score and drift_score > 0.6:
            return "Rule blocked due to policy drift"
        if health_score is not None and health_score < 0.4:
            return "Rule blocked due to degraded canary health"
        return "Rule blocked by active policy enforcement"

    return "Request allowed — policy stable and healthy"