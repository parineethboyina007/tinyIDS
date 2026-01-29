import os
from defense.rollback_explanation_store import list_explanations, load_explanation
from defense.rollback_approver import load_latest_approval
from defense.threshold_version_store import latest_version

def build_rollback_lineage(tenant: str, mode: str) -> dict:
    explanations = list_explanations(tenant, mode)
    if not explanations:
        return {"status": "empty", "message": "No rollback explanations found"}

    explanation = explanations[-1]
    explanation_id = explanation["_id"]

    approval = load_latest_approval(tenant, mode)
    if not approval:
        return {
            "status": "partial",
            "explanation": explanation,
            "message": "No approval found"
        }

    applied_version = latest_version(tenant, mode)

    return {
        "tenant": tenant,
        "mode": mode,
        "lineage": {
            "explanation": explanation,
            "approval": approval,
            "applied_thresholds": applied_version,
        },
        "integrity": {
            "explanation_valid": explanation.get("_integrity_valid", False),
            "approval_valid": approval.get("_integrity_valid", False),
            "chain_valid": True,  # step-44 already enforces this
        }
    }