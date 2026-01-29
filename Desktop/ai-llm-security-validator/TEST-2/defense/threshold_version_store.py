# defense/threshold_version_store.py

import os
import json
import uuid
from datetime import datetime
from typing import Optional, List

# ==================================================
# BASE PATH
# ==================================================

BASE_DIR = "defense/threshold_versions"


def _version_dir(tenant: str, mode: str) -> str:
    """
    Return directory for a tenant + mode.
    Creates it if missing.
    """
    if mode not in ("active", "canary"):
        raise ValueError("mode must be 'active' or 'canary'")

    path = os.path.join(BASE_DIR, tenant, mode)
    os.makedirs(path, exist_ok=True)
    return path


# ==================================================
# CREATE VERSION (IMMUTABLE)
# ==================================================

def create_version(
    tenant: str,
    mode: str,
    thresholds: dict,
    reason: str,
    parent: Optional[str] = None,
) -> dict:
    """
    Create an immutable threshold version.
    """

    version_id = uuid.uuid4().hex
    timestamp = datetime.utcnow().isoformat()

    version = {
        "version": version_id,
        "tenant": tenant,
        "mode": mode,
        "reason": reason,
        "parent": parent,
        "created_at": timestamp,
        "thresholds": thresholds,
    }

    path = os.path.join(
        _version_dir(tenant, mode),
        f"{version_id}.json",
    )

    with open(path, "w") as f:
        json.dump(version, f, indent=2)

    return version


# ==================================================
# LOAD SPECIFIC VERSION
# ==================================================

def load_version(
    tenant: str,
    mode: str,
    version_id: str,
) -> Optional[dict]:
    """
    Load a specific threshold version by ID.
    """

    path = os.path.join(
        _version_dir(tenant, mode),
        f"{version_id}.json",
    )

    if not os.path.exists(path):
        return None

    with open(path) as f:
        return json.load(f)


# ==================================================
# GET LATEST VERSION
# ==================================================

def latest_version(tenant: str, mode: str) -> Optional[dict]:
    """
    Return the most recent version (by filename ordering).
    """

    path = _version_dir(tenant, mode)
    files = sorted(
        f for f in os.listdir(path)
        if f.endswith(".json")
    )

    if not files:
        return None

    latest_file = files[-1]
    with open(os.path.join(path, latest_file)) as f:
        return json.load(f)


# ==================================================
# LIST ALL VERSIONS
# ==================================================

def list_versions(tenant: str, mode: str) -> List[dict]:
    """
    List all versions for a tenant + mode.
    """

    path = _version_dir(tenant, mode)
    versions = []

    for fname in sorted(os.listdir(path)):
        if not fname.endswith(".json"):
            continue

        with open(os.path.join(path, fname)) as f:
            versions.append(json.load(f))

    return versions