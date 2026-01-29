import os
import json
from datetime import datetime

from defense.metrics_store import snapshot
from defense.threshold_version_store import (
    create_version,
    latest_version,
    list_versions,
    load_version,
)
from defense.threshold_freeze_guard import get_freeze_status
from defense.rollback_governance import load_policy, save_pending
from defense.rollback_explainer import generate_rollback_explanation

from defense.canary_isolation import isolate_canary, is_canary_isolated
from defense.canary_cooldown import is_in_cooldown
from defense.canary_health_gate import is_gate_open

# ==================================================
# PATHS
# ==================================================

BASE_DIR = "config/security_thresholds"
os.makedirs(BASE_DIR, exist_ok=True)

# ==================================================
# CONSTANTS
# ==================================================

DEFAULT_THRESHOLDS = {
    "risk_block_threshold": 0.8,
    "severity_floor": "High",
    "last_updated": None,
}

SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]

SATURATION_BLOCK_RATE = 80
SATURATION_AVG_RISK = 0.9
MIN_RISK_THRESHOLD = 0.6
MAX_SEVERITY = "Critical"

# ==================================================
# FILE HELPERS
# ==================================================

def _threshold_path(mode: str, tenant: str) -> str:
    tenant_dir = os.path.join(BASE_DIR, "tenants", tenant)
    os.makedirs(tenant_dir, exist_ok=True)
    return os.path.join(tenant_dir, f"{mode}.json")


def load_thresholds(mode: str, tenant: str = "default") -> dict:
    path = _threshold_path(mode, tenant)
    if not os.path.exists(path):
        save_thresholds(mode, tenant, DEFAULT_THRESHOLDS.copy())
    with open(path) as f:
        return json.load(f)


def save_thresholds(mode: str, tenant: str, thresholds: dict):
    with open(_threshold_path(mode, tenant), "w") as f:
        json.dump(thresholds, f, indent=2)

# ==================================================
# SEVERITY HELPERS
# ==================================================

def _increase_severity(sev: str) -> str:
    idx = SEVERITY_ORDER.index(sev)
    return SEVERITY_ORDER[min(idx + 1, len(SEVERITY_ORDER) - 1)]


def _decrease_severity(sev: str) -> str:
    idx = SEVERITY_ORDER.index(sev)
    return SEVERITY_ORDER[max(idx - 1, 0)]

# ==================================================
# SATURATION HELPERS
# ==================================================

def _is_saturated(metrics: dict, thresholds: dict) -> bool:
    return (
        metrics.get("block_rate", 0) > SATURATION_BLOCK_RATE
        and metrics.get("avg_risk", 0) > SATURATION_AVG_RISK
        and thresholds.get("severity_floor") == MAX_SEVERITY
        and thresholds.get("risk_block_threshold", 1.0) <= MIN_RISK_THRESHOLD
    )


def _select_rollback_candidate(tenant: str, mode: str):
    versions = list_versions(tenant, mode)
    for v in reversed(versions):
        snap = load_version(tenant, mode, v["version"])
        t = snap["thresholds"]
        if (
            t["severity_floor"] != MAX_SEVERITY
            or t["risk_block_threshold"] > MIN_RISK_THRESHOLD
        ):
            return snap
    return None

# ==================================================
# ADAPTIVE CONTROLLER (STEP-52 FINAL)
# ==================================================

def adapt_thresholds(mode: str = "active", tenant: str = "default") -> dict:

    if mode not in ("active", "canary"):
        return {"status": "invalid_mode", "tenant": tenant, "mode": mode}

    # --------------------------------------------------
    # COOLDOWN GUARD (STEP-51)
    # --------------------------------------------------

    if mode == "canary" and is_in_cooldown(tenant):
        return {
            "status": "cooldown_active",
            "tenant": tenant,
            "mode": mode,
            "message": "Canary in cooldown — adaptive actions temporarily disabled",
        }

    # --------------------------------------------------
    # HEALTH GATE (STEP-52)
    # --------------------------------------------------

    if mode == "canary" and not is_gate_open(tenant):
        return {
            "status": "health_gate_active",
            "tenant": tenant,
            "mode": mode,
            "message": "Canary health gate closed — awaiting clean windows",
        }

    # --------------------------------------------------
    # METRICS
    # --------------------------------------------------

    metrics = snapshot().get("windowed", {}).get(mode)
    if not metrics:
        return {"status": "no_metrics", "tenant": tenant, "mode": mode}

    thresholds = load_thresholds(mode, tenant)

    # --------------------------------------------------
    # TERMINAL SATURATION → ISOLATION
    # --------------------------------------------------

    if mode == "canary" and _is_saturated(metrics, thresholds):
        if not is_canary_isolated(tenant):
            isolate_canary(
                tenant=tenant,
                reason="terminal_saturation",
                metrics=metrics,
            )

        return {
            "status": "escalated",
            "tenant": tenant,
            "mode": mode,
            "reason": "terminal_saturation",
            "metrics": metrics,
            "thresholds": thresholds,
            "message": "Adaptation disabled — rollback-only mode",
        }

    # --------------------------------------------------
    # FREEZE GUARD
    # --------------------------------------------------

    freeze_status = get_freeze_status(tenant)
    scope = freeze_status.get("scope") or {}
    frozen = freeze_status.get("frozen", False)

    severity_locked = bool(scope.get("severity_floor"))
    risk_locked = bool(scope.get("risk_block_threshold"))
    fully_locked = frozen and severity_locked and risk_locked

    block_rate = metrics.get("block_rate", 0)
    avg_risk = metrics.get("avg_risk", 0)

    # --------------------------------------------------
    # HARDEN / RELAX
    # --------------------------------------------------

    actions = []
    changed = False

    if block_rate > 60 and not severity_locked:
        nf = _increase_severity(thresholds["severity_floor"])
        if nf != thresholds["severity_floor"]:
            thresholds["severity_floor"] = nf
            actions.append("severity_floor_increased")
            changed = True

    if avg_risk > 0.9 and not risk_locked:
        nr = max(0.6, thresholds["risk_block_threshold"] - 0.05)
        if nr != thresholds["risk_block_threshold"]:
            thresholds["risk_block_threshold"] = nr
            actions.append("risk_threshold_lowered")
            changed = True

    if block_rate < 20 and avg_risk < 0.4:
        if not risk_locked:
            thresholds["risk_block_threshold"] = min(
                0.9, thresholds["risk_block_threshold"] + 0.05
            )
            changed = True
        if not severity_locked:
            thresholds["severity_floor"] = _decrease_severity(
                thresholds["severity_floor"]
            )
            changed = True
        if changed:
            actions.append("thresholds_relaxed")

    # --------------------------------------------------
    # NO-OP
    # --------------------------------------------------

    if not changed:
        return {
            "status": "frozen" if fully_locked else "stable",
            "tenant": tenant,
            "mode": mode,
            "thresholds": thresholds,
        }

    # --------------------------------------------------
    # PERSIST
    # --------------------------------------------------

    thresholds["last_updated"] = datetime.utcnow().isoformat()
    save_thresholds(mode, tenant, thresholds)

    parent = latest_version(tenant, mode)
    create_version(
        tenant=tenant,
        mode=mode,
        thresholds=thresholds,
        reason="adaptive_update",
        parent=parent["version"] if parent else None,
    )

    return {
        "status": "adapted",
        "tenant": tenant,
        "mode": mode,
        "actions": actions,
        "thresholds": thresholds,
    }