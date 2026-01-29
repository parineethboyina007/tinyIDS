# defense/attestation_engine.py

import os
import json
import hashlib
from datetime import datetime

from defense.policy_metrics_engine import get_security_metrics
from defense.trust_safety_report_engine import generate_trust_safety_report
from defense.policy_timeline_engine import replay_policy_timeline
from defense.evidence_bundle_engine import generate_evidence_bundle

ATTEST_DIR = "governance/attestations"

os.makedirs(ATTEST_DIR, exist_ok=True)


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_attestation_pack(tenant: str) -> dict:
    ts = datetime.utcnow().isoformat()
    base = f"{ATTEST_DIR}/{tenant}__attestation"
    os.makedirs(base, exist_ok=True)

    # 1️⃣ Metrics snapshot
    metrics = get_security_metrics(tenant)

    # 2️⃣ Trust & Safety snapshot
    trust = generate_trust_safety_report(tenant)

    # 3️⃣ Evidence bundle
    bundle = generate_evidence_bundle(tenant)
    bundle_hash = _sha256(bundle["bundle"])

    # 4️⃣ Policy lifecycle snapshot (top risky rules only)
    lifecycles = {}
    for r in metrics.get("top_rules", []):
        lifecycles[r["rule_id"]] = replay_policy_timeline(
            tenant, r["rule_id"]
        )

    # 5️⃣ Attestation document
    attestation = {
        "tenant": tenant,
        "generated_at": ts,
        "metrics": metrics,
        "trust_safety_report": trust["json_path"],
        "evidence_bundle": bundle["bundle"],
        "evidence_bundle_hash": bundle_hash,
        "policy_lifecycles": list(lifecycles.keys()),
        "standards_asserted": [
            "SOC2",
            "ISO27001",
            "AI-Governance",
        ],
        "attestation_statement": (
            "This system enforces, monitors, explains, "
            "and governs LLM behavior with auditable integrity."
        ),
    }

    with open(f"{base}/attestation.json", "w") as f:
        json.dump(attestation, f, indent=2)

    with open(f"{base}/policy_lifecycle_snapshot.json", "w") as f:
        json.dump(lifecycles, f, indent=2)

    with open(f"{base}/trust_safety_snapshot.json", "w") as f:
        json.dump(metrics, f, indent=2)

    with open(f"{base}/evidence_bundle.sha256", "w") as f:
        f.write(bundle_hash)

    with open(f"{base}/README.txt", "w") as f:
        f.write(
            "External Attestation Pack\n"
            "Verify evidence bundle hash before audit use.\n"
        )

    return {
        "tenant": tenant,
        "status": "generated",
        "path": base,
        "generated_at": ts,
    }