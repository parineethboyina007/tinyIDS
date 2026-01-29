# defense/compliance_export_engine.py

import os
import json
from datetime import datetime

from defense.policy_metrics_engine import get_security_metrics
from defense.policy_timeline_engine import replay_policy_timeline
from defense.request_explainability_store import load_request_explanation

POLICY_DIR = "governance/adaptive_policies"
ROLLBACK_FILE = "governance/policy_rollbacks.json"
ARCHIVE_DIR = "governance/policy_archive"
REQUEST_EXPLAIN_DIR = "governance/request_explanations"
EXPORT_DIR = "governance/compliance_exports"

os.makedirs(EXPORT_DIR, exist_ok=True)


# ==================================================
# HELPERS
# ==================================================

def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            raw = f.read().strip()
            return json.loads(raw) if raw else default
    except Exception:
        return default


# ==================================================
# STEP-77 — COMPLIANCE EXPORT
# ==================================================

def export_compliance_evidence(
    tenant: str,
    *,
    include_requests: bool = True,
    include_timelines: bool = True,
) -> dict:
    """
    Generate auditor-ready compliance snapshot.

    This file is:
    - deterministic
    - replayable
    - human + machine readable
    """

    generated_at = datetime.utcnow().isoformat()

    export = {
        "tenant": tenant,
        "generated_at": generated_at,
        "standards_supported": [
            "SOC2",
            "ISO27001",
            "AI-Governance",
        ],
        "metrics": get_security_metrics(tenant),
        "policies": {},
        "rollbacks": _load_json(ROLLBACK_FILE, []),
        "request_explanations": [],
    }

    # ----------------------------------
    # POLICY SNAPSHOT + TIMELINES
    # ----------------------------------

    policy_path = os.path.join(POLICY_DIR, f"{tenant}.json")
    policy = _load_json(policy_path, {})

    for rule in policy.get("rules", []):
        rule_id = rule.get("id")
        if not rule_id:
            continue

        export["policies"][rule_id] = {
            "current_state": rule,
            "timeline": replay_policy_timeline(tenant, rule_id)
            if include_timelines else None,
        }

    # ----------------------------------
    # ARCHIVED POLICIES
    # ----------------------------------

    archived = []
    for fname in os.listdir(ARCHIVE_DIR):
        if fname.startswith(f"{tenant}__"):
            archived.append(
                _load_json(os.path.join(ARCHIVE_DIR, fname), {})
            )

    export["archived_policies"] = archived

    # ----------------------------------
    # REQUEST-LEVEL EXPLANATIONS
    # ----------------------------------

    if include_requests and os.path.exists(REQUEST_EXPLAIN_DIR):
        for fname in os.listdir(REQUEST_EXPLAIN_DIR):
            path = os.path.join(REQUEST_EXPLAIN_DIR, fname)
            data = _load_json(path, None)
            if data:
                export["request_explanations"].append(data)

    # ----------------------------------
    # WRITE EXPORT
    # ----------------------------------

    out_path = os.path.join(
        EXPORT_DIR,
        f"{tenant}__compliance_export.json"
    )

    with open(out_path, "w") as f:
        json.dump(export, f, indent=2)

    return {
        "tenant": tenant,
        "export_path": out_path,
        "generated_at": generated_at,
        "rules_exported": len(export["policies"]),
        "requests_exported": len(export["request_explanations"]),
    }