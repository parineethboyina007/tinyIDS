# defense/transparency_log_engine.py

import os
import json
import hashlib
from datetime import datetime
from typing import List

# ==================================================
# STORAGE
# ==================================================

LOG_DIR = "governance/transparency"
LOG_FILE = os.path.join(LOG_DIR, "merkle_log.json")
ROOT_FILE = os.path.join(LOG_DIR, "merkle_root.json")


# ==================================================
# INTERNAL HELPERS
# ==================================================

def _ensure():
    os.makedirs(LOG_DIR, exist_ok=True)

    # --- merkle_log.json
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
    else:
        try:
            if os.stat(LOG_FILE).st_size == 0:
                raise ValueError("empty log")
            with open(LOG_FILE) as f:
                json.load(f)
        except Exception:
            # auto-heal corrupted / empty log
            with open(LOG_FILE, "w") as f:
                json.dump([], f)

    # --- merkle_root.json
    if not os.path.exists(ROOT_FILE):
        with open(ROOT_FILE, "w") as f:
            json.dump({}, f)
    else:
        try:
            if os.stat(ROOT_FILE).st_size == 0:
                raise ValueError("empty root")
            with open(ROOT_FILE) as f:
                json.load(f)
        except Exception:
            with open(ROOT_FILE, "w") as f:
                json.dump({}, f)


def _sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def _hash_file(path: str) -> bytes:
    with open(path, "rb") as f:
        return _sha256(f.read())


# ==================================================
# MERKLE TREE (DETERMINISTIC)
# ==================================================

def _merkle_root(leaves: List[bytes]) -> bytes:
    if not leaves:
        return b"\x00" * 32

    level = leaves[:]

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])  # duplicate last (CT-style)

        level = [
            _sha256(level[i] + level[i + 1])
            for i in range(0, len(level), 2)
        ]

    return level[0]


def _merkle_proof(leaves: List[bytes], index: int) -> List[bytes]:
    proof = []
    level = leaves[:]
    idx = index

    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])

        sibling_index = idx ^ 1
        proof.append(level[sibling_index])

        idx //= 2
        level = [
            _sha256(level[i] + level[i + 1])
            for i in range(0, len(level), 2)
        ]

    return proof


# ==================================================
# STEP-87 — APPEND SIGNED ATTESTATION
# ==================================================

def append_attestation(
    tenant: str,
    attestation_path: str,
) -> dict:
    """
    Append a SIGNED attestation to the transparency log.
    Input MUST be a finalized attestation.json (Step-86).
    """

    _ensure()

    if not os.path.exists(attestation_path):
        raise FileNotFoundError("attestation.json not found")

    attestation_hash = _hash_file(attestation_path).hex()

    with open(LOG_FILE) as f:
        log = json.load(f)

    entry = {
        "tenant": tenant,
        "hash": attestation_hash,
        "timestamp": datetime.utcnow().isoformat(),
        "index": len(log),
    }

    log.append(entry)

    # recompute Merkle root
    leaves = [bytes.fromhex(e["hash"]) for e in log]
    root = _merkle_root(leaves).hex()

    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    with open(ROOT_FILE, "w") as f:
        json.dump(
            {
                "root": root,
                "size": len(log),
                "updated_at": datetime.utcnow().isoformat(),
            },
            f,
            indent=2,
        )

    return {
        "status": "appended",
        "tenant": tenant,
        "index": entry["index"],
        "attestation_hash": attestation_hash,
        "merkle_root": root,
    }


# ==================================================
# AUDITOR-SIDE — INCLUSION PROOF
# ==================================================

def get_inclusion_proof(index: int) -> dict:
    _ensure()

    with open(LOG_FILE) as f:
        log = json.load(f)

    if index < 0 or index >= len(log):
        raise IndexError("Invalid log index")

    leaves = [bytes.fromhex(e["hash"]) for e in log]
    proof = _merkle_proof(leaves, index)

    with open(ROOT_FILE) as f:
        root = json.load(f)["root"]

    return {
        "leaf_hash": log[index]["hash"],
        "index": index,
        "proof": [p.hex() for p in proof],
        "root": root,
    }