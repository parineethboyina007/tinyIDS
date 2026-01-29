# defense/trust_safety_report_engine.py

import os
import json
from datetime import datetime

from defense.policy_metrics_engine import get_security_metrics
from defense.policy_timeline_engine import replay_policy_timeline
from defense.request_explainability_store import load_request_explanation

REPORT_DIR = "governance/trust_safety_reports"
EXPLANATION_DIR = "governance/request_explanations"

os.makedirs(REPORT_DIR, exist_ok=True)


# ==================================================
# INTERNAL HELPERS
# ==================================================

def _report_path(tenant: str, fmt: str):
    return os.path.join(
        REPORT_DIR,
        f"{tenant}__trust_safety_report.{fmt}"
    )


def _list_request_explanations(limit: int = 5):
    """
    STEP-79 helper
    Enumerates stored request explanations safely
    """
    if not os.path.exists(EXPLANATION_DIR):
        return []

    files = sorted(
        os.listdir(EXPLANATION_DIR),
        reverse=True
    )

    results = []
    for fname in files[:limit]:
        if not fname.endswith(".json"):
            continue

        request_id = fname.replace(".json", "")
        data = load_request_explanation(request_id)
        if data:
            results.append(data)

    return results


# ==================================================
# STEP-79 — TRUST & SAFETY REPORT
# ==================================================

def generate_trust_safety_report(
    tenant: str,
    *,
    include_examples: int = 3,
):
    """
    Human-readable Trust & Safety Report
    (Auditor / Legal / Enterprise ready)
    """

    metrics = get_security_metrics(tenant)
    explanations = _list_request_explanations(include_examples)

    lifecycle_examples = []
    for e in explanations:
        rule_id = e.get("data", {}).get("rule_id")
        if rule_id:
            lifecycle_examples.append(
                replay_policy_timeline(tenant, rule_id)
            )

    report = {
        "tenant": tenant,
        "generated_at": datetime.utcnow().isoformat(),

        "executive_summary": {
            "total_requests": metrics["total_requests"],
            "blocked_requests": metrics["blocked_requests"],
            "block_rate": metrics["block_rate"],
            "critical_blocks": metrics["critical_blocks"],
            "system_status": (
                "healthy"
                if metrics["block_rate"] < 0.5
                else "aggressive"
            ),
        },

        "security_metrics": metrics,
        "policy_lifecycle_examples": lifecycle_examples,
        "decision_examples": explanations,

        "compliance_alignment": {
            "SOC2": [
                "CC7.2 – Automated threat detection",
                "CC7.3 – Incident response evidence",
            ],
            "ISO27001": [
                "A.12 – Logging and monitoring",
                "A.16 – Incident management",
            ],
            "AI-Governance": [
                "Explainability",
                "Auditability",
                "Human oversight",
            ],
        },
    }

    # ---------------------------
    # Save JSON
    # ---------------------------
    with open(_report_path(tenant, "json"), "w") as f:
        json.dump(report, f, indent=2)

    # ---------------------------
    # Save Markdown
    # ---------------------------
    _export_markdown(report)

    return {
        "tenant": tenant,
        "status": "generated",
        "json_path": _report_path(tenant, "json"),
        "md_path": _report_path(tenant, "md"),
        "generated_at": report["generated_at"],
    }


# ==================================================
# MARKDOWN EXPORT
# ==================================================

def _export_markdown(report: dict):
    lines = []

    es = report["executive_summary"]

    lines.append(f"# Trust & Safety Report — {report['tenant']}\n")
    lines.append(f"Generated at: {report['generated_at']}\n")

    lines.append("## Executive Summary\n")
    lines.append(f"- Total Requests: **{es['total_requests']}**")
    lines.append(f"- Blocked Requests: **{es['blocked_requests']}**")
    lines.append(f"- Block Rate: **{es['block_rate']:.2f}**")
    lines.append(f"- Critical Incidents: **{es['critical_blocks']}**")
    lines.append(f"- System Status: **{es['system_status']}**\n")

    lines.append("## Compliance Alignment\n")
    for k, v in report["compliance_alignment"].items():
        lines.append(f"### {k}")
        for item in v:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## Sample Decisions\n")
    for ex in report["decision_examples"]:
        rid = ex.get("request_id")
        decision = ex.get("data", {}).get("decision")
        lines.append(f"- Request `{rid}` → **{decision}**")

    with open(_report_path(report["tenant"], "md"), "w") as f:
        f.write("\n".join(lines))