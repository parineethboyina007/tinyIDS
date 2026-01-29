# proxy/router.py

import uuid
import random

from llm_providers import get_llm_provider

from defense.firewall import ResponseValidationFirewall
from defense.shadow_firewall import ShadowFirewall
from defense.metrics_store import record

from defense.canary_promotion import get_promotion_state
from defense.canary_health_gate import is_gate_open

# 🔥 STEP-56 — Policy Evolution Engine
from defense.policy_evolution_engine import evolve_policy_from_event

# 🔥 STEP-59 — Policy Enforcement Monitor
from defense.policy_enforcement_monitor import monitor_policy_enforcement

# 🔥 STEP-75 — Request Explainability Store
from defense.request_explainability_store import save_request_explanation

from explainability.engine import ExplainabilityEngine
from audit.store import save_event


CRITICAL_RISK = 1.0


class ProxyRouter:
    """
    Core routing layer with:
    • tenant-aware security
    • canary promotion
    • autonomous policy learning (Step-56)
    • self-correcting enforcement + rollback (Step-59)
    • per-request explainability persistence (Step-75)
    """

    def __init__(self, provider_name, provider_config):
        self.llm = get_llm_provider(provider_name, provider_config)
        self.firewall = ResponseValidationFirewall()
        self.shadow = ShadowFirewall()
        self.explainer = ExplainabilityEngine()

    # ==================================================
    # CANARY TRAFFIC DECISION (STEP-53)
    # ==================================================

    def _should_route_to_canary(self, tenant: str) -> bool:
        if not is_gate_open(tenant):
            return False

        state = get_promotion_state(tenant)
        percentage = state.get("percentage", 0)

        if percentage <= 0:
            return False

        return random.uniform(0, 100) < percentage

    # ==================================================
    # MAIN ROUTER
    # ==================================================

    def forward(self, prompt: str, mode: str = "enforce", tenant: str = "default"):
        request_id = str(uuid.uuid4())

        # --------------------------------------------------
        # PROMOTION-AWARE MODE SELECTION
        # --------------------------------------------------

        effective_mode = mode
        if mode == "active" and self._should_route_to_canary(tenant):
            effective_mode = "canary"

        # --------------------------------------------------
        # REQUEST INSPECTION
        # --------------------------------------------------

        req_check = self.firewall.inspect_request(prompt, tenant=tenant)
        policy_mode = req_check["policy_mode"]
        risk = req_check.get("risk", 0.0)

        should_block_request = (
            not req_check["allowed"]
            and (effective_mode == "enforce" or risk >= CRITICAL_RISK)
        )

        if should_block_request:
            explanation = self.explainer.explain_firewall(
                stage="request",
                violations=req_check["violations"],
                policy_mode=policy_mode,
                risk=risk,
            )

            # 🔥 STEP-75 — persist explanation
            save_request_explanation(request_id, explanation)

            record(policy_mode, True, risk)

            event = {
                "request_id": request_id,
                "tenant": tenant,
                "stage": "request",
                "mode": effective_mode,
                "prompt": prompt,
                "blocked": True,
                "risk": risk,
                "policy_mode": policy_mode,
                "violations": req_check["violations"],
                "shadow": {
                    "blocked": False,
                    "risk": 0.0,
                    "violations": [],
                },
                "explanation": explanation,
            }

            save_event(request_id, event)

            # 🔥 STEP-59 — observe enforcement
            monitor_policy_enforcement(event)

            # 🧠 STEP-56 — learn only from critical threats
            if risk >= CRITICAL_RISK:
                evolve_policy_from_event({
                    "tenant": tenant,
                    "violations": req_check["violations"],
                })

            return {
                "request_id": request_id,
                "content": "[BLOCKED BY SECURITY FIREWALL]",
                "blocked": True,
                "risk": risk,
                "mode": effective_mode,
                "explanation": explanation,
            }

        # --------------------------------------------------
        # LLM EXECUTION
        # --------------------------------------------------

        response = self.llm.query(prompt)

        # --------------------------------------------------
        # RESPONSE INSPECTION
        # --------------------------------------------------

        res_check = self.firewall.inspect_response(response, tenant=tenant)
        risk = max(risk, res_check.get("risk", 0.0))

        should_block_response = (
            not res_check["allowed"]
            and (effective_mode == "enforce" or risk >= CRITICAL_RISK)
        )

        explanation = self.explainer.explain_firewall(
            stage="response",
            violations=res_check["violations"] if should_block_response else [],
            policy_mode=policy_mode,
            risk=risk,
        )

        # 🔥 STEP-75 — persist explanation
        save_request_explanation(request_id, explanation)

        record(policy_mode, should_block_response, risk)

        # --------------------------------------------------
        # SHADOW / CANARY OBSERVATION
        # --------------------------------------------------

        shadow = self.shadow.evaluate(prompt, response)
        record("canary", shadow.get("blocked", False), shadow.get("risk", 0.0))

        # --------------------------------------------------
        # AUDIT LOG
        # --------------------------------------------------

        event = {
            "request_id": request_id,
            "tenant": tenant,
            "stage": "response",
            "mode": effective_mode,
            "prompt": prompt,
            "response": response,
            "blocked": should_block_response,
            "risk": risk,
            "policy_mode": policy_mode,
            "violations": res_check.get("violations", []),
            "shadow": shadow,
            "explanation": explanation,
        }

        save_event(request_id, event)

        # 🔥 STEP-59 — observe enforcement outcome
        monitor_policy_enforcement(event)

        # 🧠 STEP-56 — adaptive learning
        if risk >= CRITICAL_RISK:
            evolve_policy_from_event({
                "tenant": tenant,
                "violations": res_check.get("violations", []),
            })
        elif shadow.get("blocked") and shadow.get("violations"):
            evolve_policy_from_event({
                "tenant": tenant,
                "violations": shadow["violations"],
            })

        return {
            "request_id": request_id,
            "content": response if not should_block_response else "[BLOCKED BY SECURITY FIREWALL]",
            "blocked": should_block_response,
            "risk": risk,
            "mode": effective_mode,
            "explanation": explanation,
        }