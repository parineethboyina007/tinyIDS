# defense/policy_drift_detector.py

from defense.policy_drift_store import load_drift_state, save_drift_state

BASELINE_WEIGHT = 0.7
RECENT_WEIGHT = 0.3
DRIFT_ALERT_THRESHOLD = 0.7


def _rate(blocked: int, total: int) -> float:
    return blocked / total if total else 0.0


def evaluate_policy_drift(
    tenant: str,
    rule_id: str,
    blocked: bool,
    false_positive: bool,
):
    """
    STEP-67 — Temporal Drift Detector
    """

    state = load_drift_state(tenant, rule_id)

    if blocked:
        state["recent"]["blocked"] += 1
    else:
        state["recent"]["clean"] += 1

    if false_positive:
        state["recent"]["false_positives"] += 1

    b_base = state["baseline"]
    b_recent = state["recent"]

    base_rate = _rate(b_base["blocked"], b_base["blocked"] + b_base["clean"])
    recent_rate = _rate(b_recent["blocked"], b_recent["blocked"] + b_recent["clean"])

    fp_base = _rate(b_base["false_positives"], b_base["blocked"])
    fp_recent = _rate(b_recent["false_positives"], b_recent["blocked"])

    drift_score = (
        abs(recent_rate - base_rate) * BASELINE_WEIGHT +
        abs(fp_recent - fp_base) * RECENT_WEIGHT
    )

    state["drift_score"] = round(drift_score, 3)

    if (b_recent["blocked"] + b_recent["clean"]) >= 20:
        state["baseline"] = b_recent
        state["recent"] = {
            "blocked": 0,
            "clean": 0,
            "false_positives": 0,
        }

    save_drift_state(state)

    return {
        "tenant": tenant,
        "rule_id": rule_id,
        "drift_score": state["drift_score"],
        "alert": state["drift_score"] >= DRIFT_ALERT_THRESHOLD,
    }