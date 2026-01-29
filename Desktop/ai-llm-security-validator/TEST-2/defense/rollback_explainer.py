import os
import json
import hashlib
from datetime import datetime
from defense.chain_integrity import seal_with_parent
from defense.threshold_version_store import latest_version

# ==================================================
# PATH
# ==================================================

EXPLANATION_DIR = "audit/rollback_explanations"
os.makedirs(EXPLANATION_DIR, exist_ok=True)

# ==================================================
# CANONICAL HASH (DEFENSIVE)
# ==================================================

def _canonical_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()

# ==================================================
# EXPLAINER (STEP-45B)
# ==================================================

def generate_rollback_explanation(
    tenant: str,
    mode: str,
    metrics: dict,
    current: dict,
    candidate: dict,
    rejected: list,
):
    """
    Create a cryptographically chained rollback explanation.

    Guarantees:
    - Side-effect safe
    - Thresholds never mutated
    - Explanation chained to latest threshold version
    """

    parent = latest_version(tenant, mode)
    parent_hash = parent["integrity"]["hash"] if parent else None

    explanation = {
        "tenant": tenant,
        "mode": mode,
        "generated_at": datetime.utcnow().isoformat(),
        "trigger": "saturation_detected",
        "metrics": {
            "block_rate": metrics.get("block_rate"),
            "avg_risk": metrics.get("avg_risk"),
        },
        "current_thresholds": current,
        "recommended_thresholds": candidate,
        "decision": {
            "why": [
                "Block rate exceeded saturation threshold",
                "Average risk remained critically high",
                "Current thresholds reached maximum restrictiveness",
                "Rollback candidate provides lower operational risk",
            ],
            "rejected_candidates": rejected,
        },
        "safety_notes": [
            "Rollback was not applied automatically",
            "Human approval required",
            "No thresholds were mutated at recommendation time",
        ],
    }

    explanation = seal_with_parent(explanation, parent_hash)

    filename = (
        f"{tenant}_{mode}_rollback_explanation_"
        f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    )

    path = os.path.join(EXPLANATION_DIR, filename)

    with open(path, "w") as f:
        json.dump(explanation, f, indent=2)

    return path