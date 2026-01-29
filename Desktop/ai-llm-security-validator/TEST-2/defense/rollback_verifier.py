import json
import hashlib

# ==================================================
# CANONICAL HASHING
# ==================================================

def _canonical_hash(data: dict) -> str:
    payload = json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()

# ==================================================
# INTERNAL ENGINE
# ==================================================

def chain_integrity(path: str) -> bool:
    """
    Verify integrity of a rollback explanation or approval file.
    This is the core verification engine.
    """

    try:
        with open(path) as f:
            data = json.load(f)

        integrity = data.get("integrity") or data.get("chain")
        if not integrity:
            return False

        expected = integrity.get("hash") or integrity.get("self_hash")
        if not expected:
            return False

        # Remove integrity section before hashing
        material = dict(data)
        material.pop("integrity", None)
        material.pop("chain", None)
        material.pop("_id", None)
        material.pop("_integrity_valid", None)

        actual = _canonical_hash(material)
        return actual == expected

    except Exception:
        return False

# ==================================================
# PUBLIC API (🔥 REQUIRED BY APPROVER & LINEAGE)
# ==================================================

def verify_integrity(path: str) -> bool:
    """
    Public, stable integrity verification API.
    All other modules MUST use this.
    """
    return chain_integrity(path)