# defense/threshold_diff.py

import os
import json

# ==================================================
# VERSION STORAGE PATH
# ==================================================

BASE_DIR = "defense/threshold_versions"

# ==================================================
# INTERNAL HELPERS
# ==================================================

def _version_path(tenant: str, mode: str, version_id: str) -> str:
    """
    Resolve path to a specific threshold version file.
    """
    return os.path.join(
        BASE_DIR,
        tenant,
        mode,
        f"{version_id}.json",
    )


def load_version(tenant: str, mode: str, version_id: str) -> dict | None:
    """
    Load a specific immutable threshold version.
    """
    path = _version_path(tenant, mode, version_id)

    if not os.path.exists(path):
        return None

    with open(path) as f:
        return json.load(f)

# ==================================================
# DIFF ENGINE (STEP-33)
# ==================================================

def diff_versions(
    tenant: str,
    mode: str,
    from_version: str,
    to_version: str,
) -> dict:
    """
    Compute a field-level diff between two threshold versions.
    """

    v1 = load_version(tenant, mode, from_version)
    v2 = load_version(tenant, mode, to_version)

    if not v1 or not v2:
        return {
            "status": "error",
            "message": "One or both versions not found",
            "tenant": tenant,
            "mode": mode,
        }

    t1 = v1.get("thresholds", {})
    t2 = v2.get("thresholds", {})

    diffs = {}

    all_keys = set(t1.keys()) | set(t2.keys())
    for key in sorted(all_keys):
        if t1.get(key) != t2.get(key):
            diffs[key] = {
                "from": t1.get(key),
                "to": t2.get(key),
            }

    return {
        "status": "ok",
        "tenant": tenant,
        "mode": mode,
        "from_version": from_version,
        "to_version": to_version,
        "diff": diffs,
    }