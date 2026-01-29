# defense/policy_metrics_engine.py

import os
import json
from collections import defaultdict
from datetime import datetime

EXPLANATION_DIR = "governance/request_explanations"

# ==================================================
# SAFE JSON
# ==================================================

def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            data = f.read().strip()
            return json.loads(data) if data else default
    except Exception:
        return default


# ==================================================
# STEP-76 — METRICS AGGREGATOR
# ==================================================

def get_security_metrics(tenant: str = "default") -> dict:
    """
    Aggregates security posture metrics for SOC / dashboard use.
    Deterministic, idempotent, read-only.
    """

    total = 0
    blocked = 0
    critical_blocks = 0

    rule_hits = defaultdict(int)
    mode_hits = defaultdict(lambda: {"blocked": 0, "allowed": 0})
    risk_buckets = defaultdict(int)

    for fname in os.listdir(EXPLANATION_DIR):
        path = os.path.join(EXPLANATION_DIR, fname)
        record = _load_json(path, None)
        if not record:
            continue

        data = record.get("data", {})
        decision = data.get("decision")
        risk = data.get("risk_score", 0.0)
        policy_mode = data.get("policy_mode", "unknown")

        total += 1
        risk_buckets[str(risk)] += 1

        if decision == "blocked":
            blocked += 1
            mode_hits[policy_mode]["blocked"] += 1

            if risk >= 1.0:
                critical_blocks += 1

            for v in data.get("violations", []):
                rule_hits[v.get("id", "unknown")] += 1
        else:
            mode_hits[policy_mode]["allowed"] += 1

    return {
        "tenant": tenant,
        "generated_at": datetime.utcnow().isoformat(),
        "total_requests": total,
        "blocked_requests": blocked,
        "block_rate": round(blocked / total, 4) if total else 0.0,
        "critical_blocks": critical_blocks,
        "top_rules": sorted(
            [{"rule_id": k, "count": v} for k, v in rule_hits.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10],
        "policy_modes": mode_hits,
        "risk_distribution": dict(risk_buckets),
    }