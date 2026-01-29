import json
import hashlib

def canonical_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def seal_with_parent(payload: dict, parent_hash: str | None):
    content = payload.copy()
    content.pop("chain", None)

    self_hash = canonical_hash(content)

    payload["chain"] = {
        "algorithm": "sha256",
        "parent_hash": parent_hash,
        "self_hash": self_hash,
    }

    return payload