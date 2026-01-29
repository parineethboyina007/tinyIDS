# defense/canary_promotion_sealer.py

from datetime import datetime

from audit.store import save_event
from defense.canary_promotion import reset_promotion
from defense.threshold_version_store import (
    latest_version,
    load_version,
    create_version,
)
from defense.adaptive_thresholds import load_thresholds, save_thresholds


# ==================================================
# CANARY PROMOTION SEALER (STEP-54)
# ==================================================

def seal_and_promote_canary(tenant: str) -> dict:
    """
    Finalizes canary rollout:
    - Copies canary thresholds → active
    - Versions the promotion
    - Resets promotion state
    - Emits audit event
    """

    # --------------------------------------------------
    # LOAD THRESHOLDS
    # --------------------------------------------------

    canary_thresholds = load_thresholds("canary", tenant)
    active_thresholds = load_thresholds("active", tenant)

    # --------------------------------------------------
    # VERSION SNAPSHOT
    # --------------------------------------------------

    parent = latest_version(tenant, "active")

    create_version(
        tenant=tenant,
        mode="active",
        thresholds=canary_thresholds,
        reason="canary_promotion_sealed",
        parent=parent["version"] if parent else None,
    )

    # --------------------------------------------------
    # APPLY TO ACTIVE
    # --------------------------------------------------

    canary_thresholds["last_updated"] = datetime.utcnow().isoformat()
    save_thresholds("active", tenant, canary_thresholds)

    # --------------------------------------------------
    # RESET PROMOTION STATE
    # --------------------------------------------------

    reset_promotion(tenant)

    # --------------------------------------------------
    # AUDIT EVENT (FIXED)
    # --------------------------------------------------

    event_id = f"canary_promotion_{tenant}_{datetime.utcnow().isoformat()}"

    save_event(
        event_id,
        {
            "event": "canary_promotion_sealed",
            "tenant": tenant,
            "sealed_at": datetime.utcnow().isoformat(),
            "thresholds": canary_thresholds,
        },
    )

    return {
        "status": "sealed",
        "tenant": tenant,
        "active_thresholds": canary_thresholds,
    }