# defense/attestation_signing_engine.py

import os
import json
import hashlib
from datetime import datetime

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from defense.attestation_key_manager import load_all_public_keys

ATTESTATION_ROOT = "governance/attestations"
KEY_ROOT = "governance/attestation_keys"


# ==================================================
# PATHS
# ==================================================

def _paths(tenant: str):
    base = os.path.join(ATTESTATION_ROOT, f"{tenant}__attestation")
    return {
        "attestation": os.path.join(base, "attestation.json"),
        "signature": os.path.join(base, "attestation.sig"),
        "hash": os.path.join(base, "attestation.sha256"),
        "private_key": os.path.join(KEY_ROOT, "active_private.pem"),
    }


# ==================================================
# HELPERS
# ==================================================

def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_binary(path: str, data: bytes):
    with open(path, "wb") as f:
        f.write(data)


def _canonical_payload(attestation: dict) -> bytes:
    """
    Deterministic canonical JSON encoding.
    Any semantic change MUST change the hash.
    """
    return json.dumps(
        attestation,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _hash_payload(payload: bytes) -> bytes:
    return hashlib.sha256(payload).digest()


def _load_private_key(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError("Active attestation private key not found")

    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None)


# ==================================================
# STEP-86 — SIGN ATTESTATION (IMMUTABLE, HASH-BOUND)
# ==================================================

def sign_attestation(tenant: str) -> dict:
    paths = _paths(tenant)

    # ---- immutability guard
    if os.path.exists(paths["signature"]):
        raise RuntimeError(
            "Attestation already signed — re-signing is forbidden"
        )

    if not os.path.exists(paths["attestation"]):
        raise FileNotFoundError("attestation.json missing")

    attestation = _load_json(paths["attestation"])

    payload = _canonical_payload(attestation)
    digest = _hash_payload(payload)

    private_key = _load_private_key(paths["private_key"])

    signature = private_key.sign(
        digest,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    # Write hash FIRST, then signature
    _save_binary(paths["hash"], digest)
    _save_binary(paths["signature"], signature)

    return {
        "tenant": tenant,
        "status": "signed",
        "algorithm": "RSA-PSS-SHA256",
        "signed_at": datetime.utcnow().isoformat(),
    }


# ==================================================
# VERIFY ATTESTATION (AUDITOR-SAFE)
# ==================================================

def verify_attestation_signature(tenant: str) -> bool:
    paths = _paths(tenant)

    if not os.path.exists(paths["attestation"]):
        raise FileNotFoundError("attestation.json missing")

    if not os.path.exists(paths["hash"]):
        raise FileNotFoundError("attestation.sha256 missing")

    if not os.path.exists(paths["signature"]):
        raise FileNotFoundError("attestation.sig missing")

    # ---- recompute hash
    attestation = _load_json(paths["attestation"])
    payload = _canonical_payload(attestation)
    computed_digest = _hash_payload(payload)

    # ---- load stored hash (BINARY!)
    with open(paths["hash"], "rb") as f:
        stored_digest = f.read()

    if computed_digest != stored_digest:
        raise ValueError(
            "Attestation payload hash mismatch — TAMPERING DETECTED"
        )

    # ---- verify signature
    with open(paths["signature"], "rb") as f:
        signature = f.read()

    for pub_path in load_all_public_keys():
        try:
            with open(pub_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())

            public_key.verify(
                signature,
                stored_digest,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH,
                ),
                hashes.SHA256(),
            )
            return True
        except Exception:
            continue

    raise ValueError(
        "Invalid signature — no trusted public key matched"
    )