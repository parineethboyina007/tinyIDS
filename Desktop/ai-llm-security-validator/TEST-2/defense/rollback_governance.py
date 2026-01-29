# defense/rollback_governance.py

import os
import json
from datetime import datetime

from defense.rollback_policy import load_policy  # ✅ FIX

BASE_DIR = "governance/rollback_pending"
os.makedirs(BASE_DIR, exist_ok=True)

def _path(tenant: str, mode: str) -> str:
    return os.path.join(BASE_DIR, f"{tenant}_{mode}.json")

def save_pending(tenant, mode, candidate_version, thresholds):
    data = {
        "tenant": tenant,
        "mode": mode,
        "candidate_version": candidate_version,
        "thresholds": thresholds,
        "approvals": [],
        "created_at": datetime.utcnow().isoformat(),
    }
    with open(_path(tenant, mode), "w") as f:
        json.dump(data, f, indent=2)

def load_pending(tenant, mode):
    path = _path(tenant, mode)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def append_approval(tenant, mode, approver_id, chain):
    pending = load_pending(tenant, mode)
    if not pending:
        return None

    pending["approvals"].append({
        "approver": approver_id,
        "timestamp": datetime.utcnow().isoformat(),
        "chain": chain,
    })

    with open(_path(tenant, mode), "w") as f:
        json.dump(pending, f, indent=2)

    return pending

def clear_pending(tenant, mode):
    path = _path(tenant, mode)
    if os.path.exists(path):
        os.remove(path)