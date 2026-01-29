# defense/rollback_explanation_store.py

import os
import json
import hashlib
from typing import List

BASE_DIR = "audit/rollback_explanations"
os.makedirs(BASE_DIR, exist_ok=True)

NON_HASH_FIELDS = {
    "_id",
    "_sealed",
    "_integrity_valid",
    "integrity",
}

def _prefix(tenant: str, mode: str) -> str:
    return f"{tenant}_{mode}_rollback_explanation_"

def _canonical_payload(data: dict) -> dict:
    return {
        k: v
        for k, v in data.items()
        if k not in NON_HASH_FIELDS
    }

def _compute_hash(payload: dict) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def _verify_integrity(data: dict) -> bool:
    integrity = data.get("integrity")
    if not integrity:
        return False

    expected = integrity.get("hash")
    actual = _compute_hash(_canonical_payload(data))

    return expected == actual

# ==================================================
# PUBLIC API
# ==================================================

def list_explanations(tenant: str, mode: str) -> List[dict]:
    results = []

    for fname in sorted(os.listdir(BASE_DIR)):
        if fname.startswith(_prefix(tenant, mode)) and fname.endswith(".json"):
            path = os.path.join(BASE_DIR, fname)
            with open(path) as f:
                data = json.load(f)

            data["_id"] = fname
            data["_integrity_valid"] = _verify_integrity(data)
            results.append(data)

    return results

def load_explanation(tenant: str, mode: str, explanation_id: str) -> dict:
    if not explanation_id.startswith(_prefix(tenant, mode)):
        raise FileNotFoundError("Explanation does not belong to tenant/mode")

    path = os.path.join(BASE_DIR, explanation_id)
    if not os.path.exists(path):
        raise FileNotFoundError("Explanation not found")

    with open(path) as f:
        data = json.load(f)

    data["_id"] = explanation_id
    data["_integrity_valid"] = _verify_integrity(data)

    return data