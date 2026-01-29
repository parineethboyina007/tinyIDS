# defense/threshold_freeze_guard.py

import os
import json
from datetime import datetime, timedelta

FREEZE_DIR = "defense/threshold_freeze"
AUDIT_DIR = "audit/threshold_freeze"

os.makedirs(FREEZE_DIR, exist_ok=True)
os.makedirs(AUDIT_DIR, exist_ok=True)

def _freeze_path(tenant: str) -> str:
    return os.path.join(FREEZE_DIR, f"{tenant}.json")

def _audit(action: str, tenant: str, payload: dict):
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    with open(
        os.path.join(AUDIT_DIR, f"{tenant}_{action}_{ts}.json"),
        "w",
    ) as f:
        json.dump(payload, f, indent=2)

# ==================================================
# FREEZE (STEP-35 + STEP-38)
# ==================================================

def freeze_thresholds(
    tenant: str,
    reason: str,
    cooldown_minutes: int = 30,
    scope: dict | None = None,
    decay: dict | None = None,
):
    data = {
        "tenant": tenant,
        "frozen": True,
        "reason": reason,
        "detected_at": datetime.utcnow().isoformat(),
        "cooldown_minutes": cooldown_minutes,
        "scope": scope or {
            "severity_floor": True,
            "risk_block_threshold": True,
        },
        "decay": decay or {
            "risk_block_threshold": 10,
            "severity_floor": 25,
        },
    }

    with open(_freeze_path(tenant), "w") as f:
        json.dump(data, f, indent=2)

    _audit("freeze", tenant, data)
    return data

# ==================================================
# DECAY LOGIC (STEP-38)
# ==================================================

def apply_freeze_decay(status: dict) -> dict:
    detected = datetime.fromisoformat(status["detected_at"])
    elapsed = (datetime.utcnow() - detected).total_seconds() / 60

    scope = status.get("scope", {}).copy()
    decay = status.get("decay", {})

    for field, minutes in decay.items():
        if elapsed >= minutes:
            scope[field] = False

    status["scope"] = scope
    return status

# ==================================================
# STATUS
# ==================================================

def get_freeze_status(tenant: str) -> dict:
    path = _freeze_path(tenant)
    if not os.path.exists(path):
        return {
            "tenant": tenant,
            "frozen": False,
            "reason": None,
            "detected_at": None,
            "cooldown_minutes": None,
            "scope": {},
        }

    with open(path) as f:
        status = json.load(f)

    status = apply_freeze_decay(status)

    # Auto-unfreeze if everything decayed + cooldown elapsed
    detected = datetime.fromisoformat(status["detected_at"])
    cooldown = timedelta(minutes=status["cooldown_minutes"])

    if (
        datetime.utcnow() > detected + cooldown
        and not any(status["scope"].values())
    ):
        return unfreeze_thresholds(
            tenant=tenant,
            reason="auto_decay_complete",
            force=True,
        )

    return status

def is_frozen(tenant: str) -> bool:
    status = get_freeze_status(tenant)
    return bool(status.get("frozen"))

# ==================================================
# UNFREEZE (STEP-36)
# ==================================================

def unfreeze_thresholds(
    tenant: str,
    reason: str,
    drift_active: bool = False,
    force: bool = False,
):
    path = _freeze_path(tenant)
    if not os.path.exists(path):
        return {"status": "noop"}

    if drift_active and not force:
        return {"status": "blocked", "reason": "threshold_drift_active"}

    os.remove(path)

    audit = {
        "tenant": tenant,
        "unfrozen": True,
        "reason": reason,
        "force": force,
        "timestamp": datetime.utcnow().isoformat(),
    }

    _audit("unfreeze", tenant, audit)

    return {
        "status": "unfrozen",
        "tenant": tenant,
        "force": force,
    }