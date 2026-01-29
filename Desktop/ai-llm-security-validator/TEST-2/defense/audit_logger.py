import os
import json
from datetime import datetime
from defense.chain_integrity import seal_with_parent

AUDIT_DIR = "audit/security_events"
os.makedirs(AUDIT_DIR, exist_ok=True)

# ==================================================
# CHAINED AUDIT LOGGER (STEP-45D)
# ==================================================

def write_audit_event(
    tenant: str,
    event_type: str,
    payload: dict,
    parent_hash: str | None,
):
    """
    Write a cryptographically chained audit event.
    """

    event = {
        "tenant": tenant,
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": payload,
    }

    event = seal_with_parent(event, parent_hash)

    fname = (
        f"{tenant}_{event_type}_"
        f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    )

    with open(os.path.join(AUDIT_DIR, fname), "w") as f:
        json.dump(event, f, indent=2)

    return fname