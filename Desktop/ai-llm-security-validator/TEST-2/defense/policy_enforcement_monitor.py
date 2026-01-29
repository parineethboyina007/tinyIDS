# defense/policy_enforcement_monitor.py

import os
import json
from datetime import datetime

from defense.policy_federated_confidence import publish_confidence_signal
from defense.policy_drift_detector import evaluate_policy_drift          # STEP-67
from defense.policy_drift_responder import respond_to_policy_drift       # STEP-68
from defense.policy_health_engine import evaluate_canary_rule_health
from defense.policy_entropy_engine import (                              # STEP-69
    update_policy_entropy,
    entropy_action,
)

# STEP-71 — Policy Memory
from defense.policy_memory_engine import (
    archive_retired_rule,
    resurrect_rule_if_needed,
)

# ==================================================
# DIRECTORIES
# ==================================================

DECAY_DIR = "governance/policy_decay"
ROLLBACK_FILE = "governance/policy_rollbacks.json"
POLICY_FILE_TEMPLATE = "governance/adaptive_policies/{tenant}.json"
MUTATION_FILE = "governance/policy_mutations.json"

os.makedirs(DECAY_DIR, exist_ok=True)

# ==================================================
# THRESHOLDS
# ==================================================

FALSE_POSITIVE_LIMIT = 3
LOW_RISK_THRESHOLD = 0.2

# ==================================================
# SAFE JSON HELPERS
# ==================================================

def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            content = f.read().strip()
            return json.loads(content) if content else default
    except Exception:
        return default


def _save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _decay_path(tenant: str, rule_id: str) -> str:
    return os.path.join(DECAY_DIR, f"{tenant}__{rule_id}.json")


def _record_mutation(entry: dict):
    data = _load_json(MUTATION_FILE, [])
    data.append(entry)
    _save_json(MUTATION_FILE, data)


def _record_rollback_once(tenant: str, rule_id: str, reason: str):
    """
    STEP-70 — idempotent rollback logging
    """
    data = _load_json(ROLLBACK_FILE, [])
    if any(r["rule_id"] == rule_id for r in data):
        return

    data.append({
        "tenant": tenant,
        "rule_id": rule_id,
        "reason": reason,
        "retired_at": datetime.utcnow().isoformat(),
    })
    _save_json(ROLLBACK_FILE, data)

# ==================================================
# RULE MUTATION HELPERS
# ==================================================

def _narrow_rule(rule: dict) -> dict:
    if rule.get("retired"):
        return rule

    if "match" in rule and "keywords" in rule["match"]:
        rule["match"]["keywords"] = rule["match"]["keywords"][:1]

    rule["severity"] = "High"
    rule["narrowed"] = True
    rule["narrowed_at"] = datetime.utcnow().isoformat()
    rule["require_context"] = ["write", "create", "build", "generate"]
    rule.setdefault("lineage", {}).setdefault("lifecycle", []).append("narrowed")
    return rule


def _apply_soft_rollback(tenant: str, rule_id: str) -> bool:
    policy_path = POLICY_FILE_TEMPLATE.format(tenant=tenant)
    policy = _load_json(policy_path, None)
    if not policy:
        return False

    for rule in policy.get("rules", []):
        if rule.get("id") != rule_id:
            continue
        if rule.get("retired") or rule.get("narrowed"):
            return False

        before = json.loads(json.dumps(rule))
        _narrow_rule(rule)

        _record_mutation({
            "tenant": tenant,
            "rule_id": rule_id,
            "action": "narrowed",
            "before": before,
            "after": rule,
            "timestamp": datetime.utcnow().isoformat(),
        })

        policy["last_updated"] = datetime.utcnow().isoformat()
        _save_json(policy_path, policy)
        return True

    return False


def _apply_hard_rollback(tenant: str, rule_id: str):
    """
    STEP-70 + STEP-71 — guaranteed retirement + memory archive
    """

    policy_path = POLICY_FILE_TEMPLATE.format(tenant=tenant)
    policy = _load_json(policy_path, {"rules": []})

    rule = next((r for r in policy.get("rules", []) if r.get("id") == rule_id), None)

    # ---------------------------------------
    # CASE 1 — Rule still exists
    # ---------------------------------------
    if rule and not rule.get("retired"):
        rule["retired"] = True
        rule["retired_at"] = datetime.utcnow().isoformat()
        rule["retired_reason"] = "excessive_false_positives_or_entropy"
        rule.setdefault("lineage", {}).setdefault("lifecycle", []).append("retired")

        policy["last_updated"] = datetime.utcnow().isoformat()
        _save_json(policy_path, policy)

        archive_retired_rule(
            tenant=tenant,
            rule=rule,
            reason=rule["retired_reason"],
        )

    # ---------------------------------------
    # CASE 2 — Rule already missing
    # ---------------------------------------
    elif not rule:
        fallback = {
            "id": rule_id,
            "retired": True,
            "retired_at": datetime.utcnow().isoformat(),
            "retired_reason": "entropy_forced_retirement_missing_policy",
            "lineage": {"lifecycle": ["retired"]},
        }

        archive_retired_rule(
            tenant=tenant,
            rule=fallback,
            reason=fallback["retired_reason"],
        )

    _record_rollback_once(
        tenant=tenant,
        rule_id=rule_id,
        reason="excessive_false_positives_or_entropy",
    )

# ==================================================
# CORE MONITOR — STEP-59B → STEP-71
# ==================================================

def monitor_policy_enforcement(event: dict):
    if not isinstance(event, dict):
        return

    tenant = event.get("tenant", "default")
    blocked = event.get("blocked", False)
    risk = event.get("risk", 1.0)
    shadow = event.get("shadow", {})
    violations = event.get("violations", [])

    now = datetime.utcnow().isoformat()

    # ==================================================
    # CLEAN EVENTS
    # ==================================================

    if not blocked and not shadow.get("blocked"):
        for fname in os.listdir(DECAY_DIR):
            if not fname.startswith(f"{tenant}__"):
                continue

            rule_id = fname.split("__", 1)[1].replace(".json", "")

            policy = _load_json(POLICY_FILE_TEMPLATE.format(tenant=tenant), {})
            rule = next((r for r in policy.get("rules", []) if r.get("id") == rule_id), None)
            if not rule or rule.get("retired"):
                continue

            path = _decay_path(tenant, rule_id)
            decay = _load_json(path, {
                "tenant": tenant,
                "rule_id": rule_id,
                "false_positives": 0,
                "clean_events": 0,
                "first_seen": None,
                "last_updated": None,
            })

            decay["clean_events"] += 1
            decay["last_updated"] = now
            decay["first_seen"] = decay["first_seen"] or now
            _save_json(path, decay)

            drift = evaluate_policy_drift(
                tenant=tenant,
                rule_id=rule_id,
                blocked=False,
                false_positive=False,
            )

            entropy = update_policy_entropy(
                tenant=tenant,
                rule_id=rule_id,
                blocked=False,
            )

            if entropy:
                action = entropy_action(entropy["entropy"])
                if action == "narrow":
                    _apply_soft_rollback(tenant, rule_id)
                elif action == "retire":
                    _apply_hard_rollback(tenant, rule_id)

            health = evaluate_canary_rule_health(tenant, rule_id)

            respond_to_policy_drift(
                tenant=tenant,
                rule_id=rule_id,
                drift_score=drift["drift_score"],
                false_positives=decay["false_positives"],
                health_score=health["health_score"] if health else None,
            )

            resurrect_rule_if_needed(
                tenant=tenant,
                rule_id=rule_id,
                confidence=health["health_score"] if health else 0.0,
                entropy=entropy["entropy"] if entropy else 1.0,
            )

        return

    # ==================================================
    # BLOCKED EVENTS
    # ==================================================

    adaptive_violation = next(
        (v for v in violations if v.get("evidence") == "adaptive_policy_match"),
        None
    )
    if not adaptive_violation:
        return

    rule_id = adaptive_violation.get("id")
    family = adaptive_violation.get("family")
    if not rule_id:
        return

    policy = _load_json(POLICY_FILE_TEMPLATE.format(tenant=tenant), {})
    rule = next((r for r in policy.get("rules", []) if r.get("id") == rule_id), None)
    if not rule or rule.get("retired"):
        return

    shadow_blocked = shadow.get("blocked", False)
    shadow_risk = shadow.get("risk", 0.0)

    is_false_positive = (
        not shadow_blocked
        and shadow_risk < LOW_RISK_THRESHOLD
        and risk < 1.0
    )

    drift = evaluate_policy_drift(
        tenant=tenant,
        rule_id=rule_id,
        blocked=True,
        false_positive=is_false_positive,
    )

    entropy = update_policy_entropy(
        tenant=tenant,
        rule_id=rule_id,
        blocked=True,
        false_positive=is_false_positive,
    )

    if entropy:
        action = entropy_action(entropy["entropy"])
        if action == "narrow":
            _apply_soft_rollback(tenant, rule_id)
        elif action == "retire":
            _apply_hard_rollback(tenant, rule_id)

    if is_false_positive and family:
        publish_confidence_signal(
            tenant=tenant,
            family=family,
            outcome="false_positive",
        )

    respond_to_policy_drift(
        tenant=tenant,
        rule_id=rule_id,
        drift_score=drift["drift_score"],
        false_positives=0,
        health_score=evaluate_canary_rule_health(tenant, rule_id)["health_score"],
    )

    resurrect_rule_if_needed(
        tenant=tenant,
        rule_id=rule_id,
        confidence=evaluate_canary_rule_health(tenant, rule_id)["health_score"],
        entropy=entropy["entropy"],
    )