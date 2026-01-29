# defense/policy_timeline_engine.py

import os
import json
from datetime import datetime

POLICY_DIR = "governance/adaptive_policies"
MUTATION_FILE = "governance/policy_mutations.json"
ROLLBACK_FILE = "governance/policy_rollbacks.json"
ARCHIVE_DIR = "governance/policy_archive"


# ==================================================
# SAFE JSON HELPERS
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


def _archive_path(tenant: str, rule_id: str):
    return os.path.join(ARCHIVE_DIR, f"{tenant}__{rule_id}.json")


# ==================================================
# STEP-72 + STEP-73 — NORMALIZED POLICY TIMELINE
# ==================================================

def replay_policy_timeline(tenant: str, rule_id: str) -> dict:
    """
    STEP-72: Timeline replay
    STEP-73: Canonical lifecycle normalization

    Guarantees:
    • No duplicate lifecycle events
    • Chronological ordering
    • Audit-safe narrative
    """

    events = []
    seen = set()

    def add_once(event_type: str, payload: dict):
        """
        Prevent duplicate lifecycle events
        """
        if event_type in seen:
            return
        seen.add(event_type)
        events.append(payload)

    # ------------------------------------------------
    # 1. Active / resurrected policy state
    # ------------------------------------------------
    policy_path = os.path.join(POLICY_DIR, f"{tenant}.json")
    policy = _load_json(policy_path, {})

    rule = next(
        (r for r in policy.get("rules", []) if r.get("id") == rule_id),
        None
    )

    if rule:
        add_once("active", {
            "event": "active",
            "timestamp": (
                rule.get("resurrected_at")
                or rule.get("committed_at")
            ),
            "state": "present_in_active_policy",
        })

    # ------------------------------------------------
    # 2. Mutation history (narrow / widen / demote)
    # ------------------------------------------------
    mutations = _load_json(MUTATION_FILE, [])
    for m in mutations:
        if m.get("tenant") == tenant and m.get("rule_id") == rule_id:
            action = m.get("action")
            add_once(action, {
                "event": action,
                "timestamp": m.get("timestamp"),
                "details": {
                    "before": m.get("before"),
                    "after": m.get("after"),
                },
            })

    # ------------------------------------------------
    # 3. Retirement (rollback) — ONCE
    # ------------------------------------------------
    rollbacks = _load_json(ROLLBACK_FILE, [])
    for r in rollbacks:
        if r.get("tenant") == tenant and r.get("rule_id") == rule_id:
            add_once("retired", {
                "event": "retired",
                "timestamp": (
                    r.get("retired_at")
                    or r.get("timestamp")
                ),
                "reason": r.get("reason"),
            })

    # ------------------------------------------------
    # 4. Archive (final memory)
    # ------------------------------------------------
    archive = _load_json(_archive_path(tenant, rule_id), None)
    if archive:
        add_once("archived", {
            "event": "archived",
            "timestamp": archive.get("archived_at"),
            "reason": archive.get("reason"),
        })

    # ------------------------------------------------
    # Sort chronologically (null-safe)
    # ------------------------------------------------
    events.sort(
        key=lambda e: e.get("timestamp") or "",
    )

    return {
        "tenant": tenant,
        "rule_id": rule_id,
        "events": events,
        "normalized": True,
        "generated_at": datetime.utcnow().isoformat(),
    }