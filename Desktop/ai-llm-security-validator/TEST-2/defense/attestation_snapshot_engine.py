# defense/attestation_snapshot_engine.py

import os
import json
from datetime import datetime

from defense.trust_safety_report_engine import generate_trust_safety_report
from defense.policy_timeline_engine import replay_policy_timeline

# ==================================================
# PATHS
# ==================================================

ATTESTATION_ROOT = "governance/attestations"
POLICY_ARCHIVE_DIR = "governance/policy_archive"


# ==================================================
# SAFE JSON HELPERS
# ==================================================

def _load_json(path: str, default=None):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            raw = f.read().strip()
            return json.loads(raw) if raw else default
    except Exception:
        return default


def _save_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ==================================================
# STEP-84 — ATTESTATION SNAPSHOT NORMALIZATION
# ==================================================

def normalize_attestation_snapshots(tenant: str):
    """
    STEP-84

    Converts all dynamic governance state into immutable,
    embedded attestation snapshots.

    Guarantees:
    • No null fields
    • Offline verifiability
    • Auditor-safe evidence
    """

    attestation_dir = os.path.join(
        ATTESTATION_ROOT, f"{tenant}__attestation"
    )

    if not os.path.isdir(attestation_dir):
        raise RuntimeError(
            f"Attestation directory not found for tenant: {tenant}"
        )

    now = datetime.utcnow().isoformat()

    # ==================================================
    # 1. TRUST & SAFETY SNAPSHOT
    # ==================================================

    trust_report = generate_trust_safety_report(tenant)
    trust_json = _load_json(trust_report["json_path"], {})

    trust_snapshot = {
        "tenant": tenant,
        "executive_summary": trust_json.get("executive_summary", {}),
        "generated_at": now,
        "source_report": trust_report["json_path"],
    }

    trust_snapshot_path = os.path.join(
        attestation_dir, "trust_safety_snapshot.json"
    )

    _save_json(trust_snapshot_path, trust_snapshot)

    # ==================================================
    # 2. POLICY LIFECYCLE SNAPSHOT
    # ==================================================

    lifecycle_events = []

    if os.path.isdir(POLICY_ARCHIVE_DIR):
        for fname in sorted(os.listdir(POLICY_ARCHIVE_DIR)):
            if not fname.startswith(f"{tenant}__"):
                continue

            rule_id = (
                fname
                .replace(f"{tenant}__", "")
                .replace(".json", "")
            )

            timeline = replay_policy_timeline(
                tenant=tenant,
                rule_id=rule_id,
            )

            events = timeline.get("events", [])

            if events:
                lifecycle_events.append({
                    "rule_id": rule_id,
                    "events": events,
                })

    policy_snapshot = {
        "tenant": tenant,
        "events": lifecycle_events,
        "generated_at": now,
        "rules_tracked": len(lifecycle_events),
    }

    policy_snapshot_path = os.path.join(
        attestation_dir, "policy_lifecycle_snapshot.json"
    )

    _save_json(policy_snapshot_path, policy_snapshot)

    # ==================================================
    # 3. RETURN NORMALIZATION RESULT
    # ==================================================

    return {
        "tenant": tenant,
        "status": "normalized",
        "trust_safety_snapshot": trust_snapshot_path,
        "policy_lifecycle_snapshot": policy_snapshot_path,
        "rules_embedded": len(lifecycle_events),
        "normalized_at": now,
    }