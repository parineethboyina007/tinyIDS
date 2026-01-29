# defense/merkle_tree.py

import hashlib


def _hash(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def merkle_root(leaves: list[bytes]) -> bytes:
    if not leaves:
        return b""

    level = leaves[:]
    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            next_level.append(_hash(left + right))
        level = next_level
    return level[0]


def merkle_proof(leaves: list[bytes], index: int) -> list[bytes]:
    proof = []
    level = leaves[:]
    idx = index

    while len(level) > 1:
        next_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            next_level.append(_hash(left + right))

            if i == idx or i + 1 == idx:
                sibling = right if i == idx else left
                proof.append(sibling)

        idx //= 2
        level = next_level

    return proof