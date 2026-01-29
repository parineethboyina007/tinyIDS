# defense/evidence_bundle_engine.py

import os
import json
import zipfile
import hashlib
from datetime import datetime

BUNDLE_DIR = "governance/evidence_bundles"
EXPORT_DIRS = [
    "governance/trust_safety_reports",
    "governance/compliance_exports",
    "governance/request_explanations",
    "governance/policy_archive",
    "governance/policy_rollbacks.json",
]

os.makedirs(BUNDLE_DIR, exist_ok=True)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_evidence_bundle(tenant: str):
    timestamp = datetime.utcnow().isoformat()
    bundle_name = f"{tenant}__evidence_bundle.zip"
    bundle_path = os.path.join(BUNDLE_DIR, bundle_name)

    manifest = {
        "tenant": tenant,
        "generated_at": timestamp,
        "files": {},
        "hash_algorithm": "SHA-256",
    }

    with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for item in EXPORT_DIRS:
            if os.path.isfile(item):
                arc = os.path.basename(item)
                zipf.write(item, arc)
                manifest["files"][arc] = _sha256(item)
                continue

            if not os.path.exists(item):
                continue

            for fname in os.listdir(item):
                if not fname.startswith(tenant):
                    continue
                full = os.path.join(item, fname)
                arc = f"{os.path.basename(item)}/{fname}"
                zipf.write(full, arc)
                manifest["files"][arc] = _sha256(full)

    manifest_path = os.path.join(BUNDLE_DIR, f"{tenant}__manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    # Simple signature (hash of manifest)
    sig = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    sig_path = os.path.join(BUNDLE_DIR, f"{tenant}__manifest.sig")

    with open(sig_path, "w") as f:
        f.write(sig)

    return {
        "tenant": tenant,
        "bundle": bundle_path,
        "manifest": manifest_path,
        "signature": sig_path,
        "generated_at": timestamp,
        "files_count": len(manifest["files"]),
    }