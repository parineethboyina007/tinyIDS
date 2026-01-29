# defense/canary_cooldown.py

import os
import json
from datetime import datetime, timedelta

COOLDOWN_DIR = "governance/canary_cooldown"
os.makedirs(COOLDOWN_DIR, exist_ok=True)

COOLDOWN_MINUTES = 30

def _path(tenant: str) -> str:
    return os.path.join(COOLDOWN_DIR, f"{tenant}.json")

def start_cooldown(tenant: str) -> dict:
    record = {
        "tenant": tenant,
        "started_at": datetime.utcnow().isoformat(),
        "expires_at": (
            datetime.utcnow() + timedelta(minutes=COOLDOWN_MINUTES)
        ).isoformat(),
        "status": "active",
    }

    with open(_path(tenant), "w") as f:
        json.dump(record, f, indent=2)

    return record

def is_in_cooldown(tenant: str) -> bool:
    path = _path(tenant)
    if not os.path.exists(path):
        return False

    with open(path) as f:
        record = json.load(f)

    expires = datetime.fromisoformat(record["expires_at"])
    if datetime.utcnow() >= expires:
        record["status"] = "expired"
        with open(path, "w") as f:
            json.dump(record, f, indent=2)
        return False

    return True

def load_cooldown(tenant: str) -> dict | None:
    if not os.path.exists(_path(tenant)):
        return None
    with open(_path(tenant)) as f:
        return json.load(f)