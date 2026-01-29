# defense/attestation_key_manager.py

import os
import json
from datetime import datetime, timedelta

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

KEY_DIR = "governance/attestation_keys"
ARCHIVE_DIR = os.path.join(KEY_DIR, "archived")
REGISTRY_FILE = os.path.join(KEY_DIR, "key_registry.json")

KEY_TTL_DAYS = 90  # 🔐 rotation policy

os.makedirs(KEY_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)


# ==================================================
# Helpers
# ==================================================

def _now():
    return datetime.utcnow()


def _load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ==================================================
# KEY GENERATION
# ==================================================

def _generate_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    return private_pem, public_pem


# ==================================================
# REGISTRY
# ==================================================

def load_key_registry():
    return _load_json(REGISTRY_FILE, {
        "active_key_created_at": None,
        "active_key_expires_at": None,
        "archived_keys": []
    })


def save_key_registry(registry):
    _save_json(REGISTRY_FILE, registry)


# ==================================================
# ROTATION LOGIC (STEP-86)
# ==================================================

def rotate_attestation_keys(force: bool = False):
    registry = load_key_registry()
    now = _now()

    expires_at = (
        datetime.fromisoformat(registry["active_key_expires_at"])
        if registry["active_key_expires_at"]
        else None
    )

    if not force and expires_at and expires_at > now:
        return {
            "status": "skipped",
            "reason": "active_key_still_valid",
            "expires_at": expires_at.isoformat()
        }

    # Archive old keys if present
    if os.path.exists(f"{KEY_DIR}/active_public.pem"):
        ts = registry["active_key_created_at"].replace(":", "-")
        os.rename(
            f"{KEY_DIR}/active_public.pem",
            f"{ARCHIVE_DIR}/{ts}_public.pem"
        )
        registry["archived_keys"].append({
            "public_key": f"{ARCHIVE_DIR}/{ts}_public.pem",
            "retired_at": now.isoformat()
        })

    # Generate new keys
    private_pem, public_pem = _generate_keypair()

    with open(f"{KEY_DIR}/active_private.pem", "wb") as f:
        f.write(private_pem)

    with open(f"{KEY_DIR}/active_public.pem", "wb") as f:
        f.write(public_pem)

    registry["active_key_created_at"] = now.isoformat()
    registry["active_key_expires_at"] = (now + timedelta(days=KEY_TTL_DAYS)).isoformat()

    save_key_registry(registry)

    return {
        "status": "rotated",
        "created_at": registry["active_key_created_at"],
        "expires_at": registry["active_key_expires_at"]
    }


# ==================================================
# PUBLIC KEY LOADING (verification support)
# ==================================================

def load_all_public_keys():
    keys = []

    # Active key
    active_path = f"{KEY_DIR}/active_public.pem"
    if os.path.exists(active_path):
        keys.append(active_path)

    registry = load_key_registry()
    for k in registry.get("archived_keys", []):
        keys.append(k["public_key"])

    return keys