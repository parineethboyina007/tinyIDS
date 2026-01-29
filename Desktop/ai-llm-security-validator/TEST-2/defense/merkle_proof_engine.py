# defense/merkle_proof_engine.py

import os
import json
import hashlib
from typing import List, Dict

LOG_DIR = "governance/transparency"
LOG_FILE = f"{LOG_DIR}/merkle_log.json"
ROOT_FILE = f"{LOG_DIR}/merkle_root.json"


# ==================================================
# HELPERS
# ==================================================

def _hash(x: bytes) -> bytes:
    return hashlib.sha256(x).digest()


def _load_log() -> list:
    if not os.path.exists(LOG_FILE):
        raise FileNotFoundError("Merkle log not found")
    with open(LOG_FILE) as f:
        return json.load(f)


def _load_root() -> dict:
    if not os.path.exists(ROOT_FILE):
        raise FileNotFoundError("Merkle root not found")
    with open(ROOT_FILE) as f:
        return json.load(f)


def _merkle_levels(hashes: List[bytes]) -> List[List[bytes]]:
    """
    Build all Merkle tree levels (for proof generation)
    """
    if not hashes:
        return [[b"\x00" * 32]]

    levels = [hashes[:]]
    while len(levels[-1]) > 1:
        level = levels[-1]
        if len(level) % 2 == 1:
            level = level + [level[-1]]
        parent = [
            _hash(level[i] + level[i + 1])
            for i in range(0, len(level), 2)
        ]
        levels.append(parent)

    return levels


# ==================================================
# STEP-89 — INCLUSION PROOF GENERATION
# ==================================================

def get_inclusion_proof(attestation_hash_hex: str) -> Dict:
    """
    Generate Merkle inclusion proof for an attestation hash
    """
    log = _load_log()
    root_info = _load_root()

    leaves = [bytes.fromhex(e["hash"]) for e in log]

    try:
        index = next(
            i for i, e in enumerate(log)
            if e["hash"] == attestation_hash_hex
        )
    except StopIteration:
        raise ValueError("Attestation hash not found in Merkle log")

    levels = _merkle_levels(leaves)

    proof = []
    idx = index

    for level in levels[:-1]:
        if len(level) % 2 == 1:
            level = level + [level[-1]]

        sibling_idx = idx ^ 1
        proof.append(level[sibling_idx].hex())
        idx //= 2

    return {
        "leaf_hash": attestation_hash_hex,
        "leaf_index": index,
        "proof": proof,
        "root": root_info["root"],
        "tree_size": root_info["size"],
    }


# ==================================================
# STEP-89 — PROOF VERIFICATION (AUDITOR-SIDE)
# ==================================================

def verify_inclusion_proof(
    leaf_hash_hex: str,
    proof: List[str],
    root_hex: str,
    leaf_index: int,
) -> bool:
    """
    Verify inclusion proof WITHOUT access to system
    """
    current = bytes.fromhex(leaf_hash_hex)
    idx = leaf_index

    for sibling_hex in proof:
        sibling = bytes.fromhex(sibling_hex)
        if idx % 2 == 0:
            current = _hash(current + sibling)
        else:
            current = _hash(sibling + current)
        idx //= 2

    return current.hex() == root_hex