# defense/canary_reenable.py

from datetime import datetime
from defense.canary_isolation import (
    load_isolation,
    clear_isolation,
)

def reenable_canary(tenant: str, reason: str) -> dict:
    """
    Explicit human-controlled re-enable handshake.
    """

    record = load_isolation(tenant)
    if not record:
        return {
            "status": "not_isolated",
            "tenant": tenant,
            "message": "Canary is already active",
        }

    cleared = clear_isolation(tenant, reason)

    return {
        "status": "reenabled",
        "tenant": tenant,
        "reenabled_at": datetime.utcnow().isoformat(),
        "previous_isolation": cleared,
    }