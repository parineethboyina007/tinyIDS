# proxy/server.py

import json
import uuid
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse

# ==================================================
# CORE PROXY
# ==================================================

from proxy.schemas import LLMRequest
from proxy.router import ProxyRouter
from config.loader import load_config

# ==================================================
# AUDIT / STORAGE
# ==================================================

from audit.store import load_event, save_event

# ==================================================
# REPLAY / ANALYSIS
# ==================================================

from replay.executor import ReplayExecutor
from analyzer.attack_learner import AttackPatternLearner
from analyzer.explainability_analytics import ExplainabilityAnalytics

# ==================================================
# DEFENSE CORE
# ==================================================

from defense.metrics_store import snapshot, reset

# ==================================================
# THRESHOLDS
# ==================================================

from defense.adaptive_thresholds import adapt_thresholds, load_thresholds
from defense.threshold_drift_detector import detect_threshold_drift
from defense.threshold_freeze_guard import (
    freeze_thresholds,
    unfreeze_thresholds,
    is_frozen,
    get_freeze_status,
)

# ==================================================
# ROLLBACK / GOVERNANCE
# ==================================================

from defense.rollback_approver import approve_rollback
from defense.rollback_explanation_store import (
    list_explanations,
    load_explanation,
)
from defense.rollback_explanation_view import build_ui_view
from defense.rollback_lineage import build_rollback_lineage

# ==================================================
# CANARY / INCIDENTS
# ==================================================

from defense.canary_isolation import load_isolation, clear_isolation
from defense.canary_cooldown import start_cooldown
from defense.incident_exporter import export_incident
from defense.canary_health_gate import evaluate_health_window
from defense.canary_promotion import advance_promotion, get_promotion_state
from defense.canary_promotion_sealer import seal_and_promote_canary
from defense.policy_merge_controller import merge_policy_if_confident

# ==================================================
# 🔐 STEP-78 — COMPLIANCE EXPORT API
# ==================================================

from proxy.compliance_router import router as compliance_router

# ==================================================
# 🧾 STEP-83 — ATTESTATION EXPORT API (AUDITOR SAFE)
# ==================================================

from proxy.attestation_router import router as attestation_router

# ==================================================
# 🧭 STEP-82 — GOVERNANCE DASHBOARD (READ-ONLY)
# ==================================================

from dashboard.app import app as dashboard_app

# ==================================================
# APP SETUP
# ==================================================

app = FastAPI(
    title="LLM Security Proxy",
    description="Live enforcement proxy for LLM security",
    version="1.0",
)

# ==================================================
# REGISTER ROUTERS
# ==================================================

# STEP-78 — Compliance Export
app.include_router(compliance_router)

# STEP-83 — External Attestation Export
app.include_router(attestation_router)

# STEP-82 — Governance Dashboard (READ-ONLY)
app.mount("/governance", dashboard_app)

# ==================================================
# LOAD CONFIG
# ==================================================

config = load_config()
provider_name = config["llm"]["provider"]
provider_config = config["llm"]

router = ProxyRouter(provider_name, provider_config)

# ==================================================
# CHAT COMPLETIONS
# ==================================================

@app.post("/v1/chat/completions")
def chat_completions(req: LLMRequest, request: Request):
    prompt = "\n".join(f"{m.role.upper()}: {m.content}" for m in req.messages)
    mode = request.headers.get("X-SECURITY-MODE") or req.mode or "enforce"

    if req.stream:
        def event_stream():
            for event in router.forward_streaming(prompt, mode=mode):
                yield f"data: {json.dumps(event)}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return router.forward(prompt, mode=mode)

# ==================================================
# REPLAY
# ==================================================

@app.get("/v1/replay/{request_id}")
def replay(request_id: str):
    event = load_event(request_id)
    if not event:
        raise HTTPException(404, "Replay not found")
    return event


@app.post("/v1/replay/{request_id}/execute")
def replay_execute(request_id: str, payload: dict):
    original = load_event(request_id)
    if not original:
        raise HTTPException(404, "Replay not found")

    executor = ReplayExecutor(
        provider_name=provider_name,
        provider_config=provider_config,
        policy_path=payload.get("policy_path"),
    )

    result = executor.execute(
        prompt=original["prompt"],
        mode=payload.get("mode", "enforce"),
    )

    replay_id = str(uuid.uuid4())

    save_event(
        replay_id,
        {
            "request_id": replay_id,
            "original_request_id": request_id,
            "prompt": original["prompt"],
            "result": result,
        },
    )

    return {
        "replay_id": replay_id,
        "original_request_id": request_id,
        "result": result,
    }

# ==================================================
# METRICS
# ==================================================

@app.get("/v1/metrics")
def get_metrics():
    return snapshot()


@app.post("/v1/metrics/reset")
def reset_metrics():
    reset()
    return {"status": "reset"}

# ==================================================
# ANALYTICS
# ==================================================

@app.post("/v1/analyze/attack-patterns")
def learn_attack_patterns(payload: dict | None = None):
    learner = AttackPatternLearner(
        min_occurrences=(payload or {}).get("min_occurrences", 5)
    )
    return learner.learn()


@app.get("/v1/analyze/explanations")
def analyze_explanations(window_minutes: int = 60):
    return ExplainabilityAnalytics(window_minutes).analyze()

# ==================================================
# THRESHOLD ADAPTATION
# ==================================================

@app.post("/v1/security/adapt-thresholds/{tenant}/{mode}")
def adapt_thresholds_by_tenant(tenant: str, mode: str):
    if mode not in ("active", "canary"):
        raise HTTPException(400, "mode must be active or canary")

    if is_frozen(tenant):
        return {
            "status": "frozen",
            "tenant": tenant,
            "reason": get_freeze_status(tenant),
        }

    return adapt_thresholds(mode=mode, tenant=tenant)


@app.get("/v1/security/thresholds/{tenant}/{mode}")
def get_thresholds_by_tenant(tenant: str, mode: str):
    if mode not in ("active", "canary"):
        raise HTTPException(400, "mode must be active or canary")

    return load_thresholds(mode, tenant)

# ==================================================
# FREEZE / UNFREEZE
# ==================================================

@app.get("/v1/security/freeze/{tenant}")
def get_freeze_api(tenant: str):
    return get_freeze_status(tenant)


@app.post("/v1/security/freeze/{tenant}")
def freeze_thresholds_api(tenant: str, payload: dict):
    reason = payload.get("reason", "manual_freeze")
    cooldown = payload.get("cooldown_minutes", 30)
    return freeze_thresholds(tenant, reason, cooldown)


@app.post("/v1/security/freeze/{tenant}/unfreeze")
def unfreeze_thresholds_api(tenant: str, payload: dict):
    reason = payload.get("reason")
    force = payload.get("force", False)

    if not reason:
        raise HTTPException(400, "reason is required")

    drift = detect_threshold_drift(tenant, mode="active")

    result = unfreeze_thresholds(
        tenant=tenant,
        reason=reason,
        drift_active=(drift["status"] == "alert"),
        force=force,
    )

    if result.get("status") == "blocked":
        raise HTTPException(409, result)

    return result

# ==================================================
# ROLLBACK GOVERNANCE
# ==================================================

@app.post("/v1/security/rollback/approve/{tenant}/{mode}")
def approve_rollback_api(tenant: str, mode: str):
    result = approve_rollback(tenant, mode)
    if not result:
        raise HTTPException(404, "No pending rollback to approve")
    return result

# ==================================================
# ROLLBACK EXPLANATIONS
# ==================================================

@app.get("/v1/security/rollback/explanations/{tenant}/{mode}")
def get_rollback_explanations(tenant: str, mode: str):
    explanations = list_explanations(tenant, mode)
    return {
        "tenant": tenant,
        "mode": mode,
        "count": len(explanations),
        "explanations": explanations,
    }


@app.get("/v1/security/rollback/explanations/{tenant}/{mode}/{explanation_id}")
def get_rollback_explanation_api(
    tenant: str,
    mode: str,
    explanation_id: str,
    view: str | None = None,
):
    explanation = load_explanation(tenant, mode, explanation_id)
    if view == "ui":
        return build_ui_view(explanation)
    return explanation


@app.get("/v1/security/rollback/lineage/{tenant}/{mode}")
def get_rollback_lineage(tenant: str, mode: str):
    return build_rollback_lineage(tenant, mode)

# ==================================================
# CANARY RE-ENABLE
# ==================================================

@app.post("/v1/security/canary/reenable/{tenant}")
def reenable_canary_api(tenant: str, payload: dict):
    reason = payload.get("reason")
    if not reason:
        raise HTTPException(status_code=400, detail="reason is required")

    existing = load_isolation(tenant)
    if not existing or existing.get("status") != "isolated":
        return {
            "status": "not_isolated",
            "tenant": tenant,
            "message": "Canary is not currently isolated",
        }

    cleared = clear_isolation(tenant, reason)
    cooldown = start_cooldown(tenant)

    return {
        "status": "reenabled",
        "tenant": tenant,
        "reenabled_at": datetime.utcnow().isoformat(),
        "cooldown": cooldown,
        "previous_isolation": cleared,
    }

# ==================================================
# INCIDENT EXPORT
# ==================================================

@app.post("/v1/security/incidents/export/{tenant}/{mode}")
def export_incident_api(tenant: str, mode: str):
    return export_incident(tenant, mode)

# ==================================================
# CANARY HEALTH & PROMOTION
# ==================================================

@app.get("/v1/security/canary/health/{tenant}")
def get_canary_health(tenant: str):
    state = evaluate_health_window(tenant)
    return {
        "tenant": tenant,
        "gate_status": state["status"],
        "clean_windows": state["clean_windows"],
        "required": state["required"],
        "opened_at": state.get("opened_at"),
    }


@app.post("/v1/security/canary/promote/{tenant}")
def promote_canary(tenant: str):
    return advance_promotion(tenant)


@app.get("/v1/security/canary/promotion/{tenant}")
def promotion_status(tenant: str):
    return get_promotion_state(tenant)


@app.post("/v1/security/canary/seal/{tenant}")
def seal_canary_api(tenant: str):
    return seal_and_promote_canary(tenant)

# ==================================================
# STEP-57 — ADAPTIVE POLICY MERGE
# ==================================================

@app.post("/v1/security/policy/merge/{tenant}/{family}")
def merge_policy_api(tenant: str, family: str):
    return merge_policy_if_confident(tenant, family)