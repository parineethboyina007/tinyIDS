# defense/policy_evolution_engine.py

from typing import Dict, List

from defense.attack_family_classifier import classify_attack_family
from defense.policy_patch_generator import generate_policy_patch
from defense.adaptive_policy_store import save_policy_patch

# STEP-57: Local confidence gate
from defense.policy_confidence_guard import should_commit_policy

# STEP-66: Federated confidence
from defense.policy_federated_confidence import publish_confidence_signal


# ==================================================
# NORMALIZATION
# ==================================================

def _normalize_violations(violations: List[dict]) -> List[dict]:
    normalized = []
    for v in violations:
        if isinstance(v, dict) and "id" in v:
            normalized.append(v)
    return normalized


# ==================================================
# POLICY EVOLUTION ENGINE
# ==================================================

def evolve_policy_from_event(event: Dict) -> Dict:
    """
    STEP-56/57/66 — Autonomous Policy Evolution
    """

    if not isinstance(event, dict):
        return {"status": "ignored", "reason": "invalid_event"}

    tenant = event.get("tenant", "default")
    violations = event.get("violations", [])

    if not isinstance(violations, list):
        return {
            "status": "ignored",
            "tenant": tenant,
            "reason": "violations_not_list",
        }

    violations = _normalize_violations(violations)

    if not violations:
        return {
            "status": "no_signal",
            "tenant": tenant,
        }

    # --------------------------------------------------
    # ATTACK FAMILY CLASSIFICATION
    # --------------------------------------------------

    family = classify_attack_family(violations)

    if not family or family == "unknown":
        return {
            "status": "ignored",
            "tenant": tenant,
            "family": family,
            "reason": "unclassified_attack",
        }

    # --------------------------------------------------
    # CONFIDENCE GATE (LOCAL + FEDERATED)
    # --------------------------------------------------

    confidence = should_commit_policy(tenant, family)

    if not confidence.get("allowed"):
        return {
            "status": "learning_deferred",
            "tenant": tenant,
            "family": family,
            "count": confidence.get("count", 0),
            "required": confidence.get("required"),
            "reason": "insufficient_evidence",
        }

    # --------------------------------------------------
    # POLICY PATCH GENERATION
    # --------------------------------------------------

    patch = generate_policy_patch(family)

    if not patch:
        return {
            "status": "ignored",
            "tenant": tenant,
            "family": family,
            "reason": "no_actionable_patch",
        }

    # --------------------------------------------------
    # PERSIST PATCH
    # --------------------------------------------------

    state = save_policy_patch(
        tenant=tenant,
        family=family,
        patch=patch,
    )

    # --------------------------------------------------
    # STEP-66 — Publish federated confidence
    # --------------------------------------------------

    publish_confidence_signal(
        tenant=tenant,
        family=family,
        outcome="effective",
    )

    return {
        "status": "policy_committed",
        "tenant": tenant,
        "family": family,
        "count": confidence.get("count"),
        "required": confidence.get("required"),
        "patch": patch,
        "state": state,
    }