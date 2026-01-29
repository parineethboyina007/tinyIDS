import os
import json
import hashlib
from datetime import datetime

from defense.rollback_governance import load_pending, clear_pending
from defense.rollback_verifier import verify_integrity

# ==================================================
# PATHS
# ==================================================

APPROVAL_DIR = "audit/rollback_approvals"
os.makedirs(APPROVAL_DIR, exist_ok=True)

# ==================================================
# HELPERS
# ==================================================

def _approval_prefix(tenant: str, mode: str) -> str:
    return f"{tenant}_{mode}_rollback_approval_"

def _hash(data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()

# ==================================================
# WRITE (already used)
# ==================================================

def approve_rollback(tenant: str, mode: str) -> dict | None:
    pending = load_pending(tenant, mode)
    if not pending:
        return None

    explanation_id = pending.get("source_explanation")

    approval = {
        "tenant": tenant,
        "mode": mode,
        "approved_at": datetime.utcnow().isoformat(),
        "applied_from": pending["candidate_version"],
        "thresholds": pending["thresholds"],
        "source_explanation": explanation_id,
    }

    # --------------------------------------------------
    # CHAIN HASHING
    # --------------------------------------------------

    parent_hash = None
    if explanation_id:
        explanation_path = f"audit/rollback_explanations/{explanation_id}"
        if os.path.exists(explanation_path):
            with open(explanation_path) as f:
                explanation = json.load(f)
                parent_hash = explanation.get("integrity", {}).get("hash")

    chain = {
        "algorithm": "sha256",
        "parent_hash": parent_hash,
        "self_hash": _hash(approval),
    }

    approval["chain"] = chain

    filename = (
        f"{tenant}_{mode}_rollback_approval_"
        f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    )

    path = os.path.join(APPROVAL_DIR, filename)
    with open(path, "w") as f:
        json.dump(approval, f, indent=2)

    clear_pending(tenant, mode)

    approval["_id"] = filename
    approval["_integrity_valid"] = verify_integrity(path)

    return approval

# ==================================================
# READ (🔥 REQUIRED BY LINEAGE)
# ==================================================

def load_latest_approval(tenant: str, mode: str) -> dict | None:
    prefix = _approval_prefix(tenant, mode)

    approvals = sorted(
        f for f in os.listdir(APPROVAL_DIR)
        if f.startswith(prefix) and f.endswith(".json")
    )

    if not approvals:
        return None

    latest = approvals[-1]
    path = os.path.join(APPROVAL_DIR, latest)

    with open(path) as f:
        data = json.load(f)

    data["_id"] = latest
    data["_integrity_valid"] = verify_integrity(path)

    return data