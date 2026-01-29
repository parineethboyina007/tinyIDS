# defense/auto_promoter.py

import uuid
import yaml
import os

from defense.metrics_store import snapshot
from defense.policy_store import (
    promote_canary,
    get_canary_policy_path,
)
from defense.regression_guard import run_regression_replay
from audit.promotion_store import save_promotion_report

# ==================================================
# THRESHOLDS
# ==================================================

MIN_CANARY_REQUESTS = 20

MAX_BLOCK_RATE_DELTA = 5.0
MAX_RISK_DELTA = 0.10

MIN_CANARY_BLOCK_RATE = 1.0
MIN_CANARY_AVG_RISK = 0.05

MAX_RELAXATION_PERCENT = 30.0

# ==================================================
# AUTO PROMOTION ENGINE
# ==================================================

def auto_promote_if_safe():
    promotion_id = str(uuid.uuid4())

    metrics = snapshot()
    windowed = metrics.get("windowed", {})

    base_report = {
        "promotion_id": promotion_id,
        "metrics": windowed,
    }

    # --------------------------------------------------
    # METRICS PRESENCE
    # --------------------------------------------------
    if "canary" not in windowed or "active" not in windowed:
        report = {
            **base_report,
            "status": "no_canary",
            "reason": "missing_active_or_canary_metrics",
        }
        save_promotion_report(report)
        return report

    canary = windowed["canary"]
    active = windowed["active"]

    # --------------------------------------------------
    # DATA SUFFICIENCY
    # --------------------------------------------------
    if canary["requests"] < MIN_CANARY_REQUESTS:
        report = {
            **base_report,
            "status": "insufficient_data",
            "canary_requests": canary["requests"],
        }
        save_promotion_report(report)
        return report

    # --------------------------------------------------
    # SECURITY FLOORS
    # --------------------------------------------------
    if canary["block_rate"] < MIN_CANARY_BLOCK_RATE:
        report = {
            **base_report,
            "status": "rejected",
            "reason": "weak_canary_enforcement",
            "canary_block_rate": canary["block_rate"],
        }
        save_promotion_report(report)
        return report

    if canary["avg_risk"] < MIN_CANARY_AVG_RISK:
        report = {
            **base_report,
            "status": "rejected",
            "reason": "canary_risk_too_low",
            "canary_avg_risk": canary["avg_risk"],
        }
        save_promotion_report(report)
        return report

    # --------------------------------------------------
    # RELATIVE REGRESSIONS
    # --------------------------------------------------
    block_rate_delta = canary["block_rate"] - active["block_rate"]
    risk_delta = canary["avg_risk"] - active["avg_risk"]

    if block_rate_delta > MAX_BLOCK_RATE_DELTA:
        report = {
            **base_report,
            "status": "not_safe",
            "reason": "block_rate_regression",
            "block_rate_delta": round(block_rate_delta, 2),
        }
        save_promotion_report(report)
        return report

    if risk_delta > MAX_RISK_DELTA:
        report = {
            **base_report,
            "status": "not_safe",
            "reason": "risk_regression",
            "risk_delta": round(risk_delta, 3),
        }
        save_promotion_report(report)
        return report

    # --------------------------------------------------
    # RELAXATION GUARD
    # --------------------------------------------------
    relaxation = active["block_rate"] - canary["block_rate"]

    if relaxation > MAX_RELAXATION_PERCENT:
        report = {
            **base_report,
            "status": "rejected",
            "reason": "canary_too_weak_vs_active",
            "relaxation_percent": round(relaxation, 2),
        }
        save_promotion_report(report)
        return report

    # --------------------------------------------------
    # REGRESSION REPLAY
    # --------------------------------------------------
    regression = run_regression_replay()
    if not regression["safe"]:
        report = {
            **base_report,
            "status": "regression_failed",
            "failures": regression.get("failures", [])[:5],
        }
        save_promotion_report(report)
        return report

    # --------------------------------------------------
    # 🔒 ESCALATION-AWARE PROMOTION GUARD (STEP-24)
    # --------------------------------------------------
    canary_path = get_canary_policy_path()
    if canary_path and os.path.exists(canary_path):
        with open(canary_path) as f:
            canary_policy = yaml.safe_load(f) or {}

        source = canary_policy.get("source")
        if source != "adaptive_severity_escalation":
            report = {
                **base_report,
                "status": "skipped",
                "reason": "canary_not_from_adaptive_escalation",
                "source": source,
            }
            save_promotion_report(report)
            return report

    # --------------------------------------------------
    # PROMOTION
    # --------------------------------------------------
    policy_id = promote_canary()

    report = {
        **base_report,
        "status": "promoted",
        "policy_id": policy_id,
        "block_rate_delta": round(block_rate_delta, 2),
        "risk_delta": round(risk_delta, 3),
        "relaxation_percent": round(relaxation, 2),
    }

    save_promotion_report(report)
    return report