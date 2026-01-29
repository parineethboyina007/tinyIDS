# defense/policy_confidence_guard.py

from defense.policy_confidence_store import (
    record_signal,
    is_confident_enough,
    get_confidence,
)
from defense.federated_confidence_store import get_federated_confidence


def should_commit_policy(tenant: str, family: str) -> dict:
    """
    STEP-57 + STEP-66 — Confidence Gate with Federated Blending

    Guarantees:
    • never crashes
    • numeric confidence only
    • federated signal is additive but bounded
    • unknown families are safe
    """

    # --------------------------------------------------
    # Record local signal
    # --------------------------------------------------

    state = record_signal(tenant, family)

    # --------------------------------------------------
    # LOCAL CONFIDENCE (numeric)
    # --------------------------------------------------

    local_state = get_confidence(tenant, family)

    if isinstance(local_state, dict):
        local_conf = float(local_state.get("confidence", 0.0))
    else:
        local_conf = float(local_state or 0.0)

    # --------------------------------------------------
    # FEDERATED CONFIDENCE (optional)
    # --------------------------------------------------

    fed = get_federated_confidence(family)

    if isinstance(fed, dict):
        federated_conf = float(fed.get("confidence", 0.0))
    else:
        federated_conf = 0.0

    # Small bounded boost
    federated_boost = min(0.2, federated_conf * 0.2)

    # --------------------------------------------------
    # BLENDED CONFIDENCE
    # --------------------------------------------------

    blended_confidence = min(1.0, local_conf + federated_boost)

    # --------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------

    allowed = (
        is_confident_enough(tenant, family)
        and blended_confidence >= 0.6
    )

    return {
        "tenant": tenant,
        "family": family,
        "count": state.get("count", 0),
        "required": state.get("required"),
        "local_confidence": local_conf,
        "federated_confidence": federated_conf,
        "blended_confidence": blended_confidence,
        "allowed": allowed,
    }