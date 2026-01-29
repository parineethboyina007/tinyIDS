# defense/firewall.py

import random

from defense.semantic_classifier import SemanticStreamClassifier
from defense.semantic_decay import SemanticRiskTracker
from defense.policy_engine import PolicyEngine
from defense.policy_store import (
    get_active_policy_path,
    get_canary_policy_path,
    load_canary_config,
)
from defense.adaptive_thresholds import load_thresholds

# 🔥 STEP-58: Adaptive Policy Runtime
from defense.adaptive_policy_runtime import match_adaptive_policy

# ==================================================
# SEVERITY CONFIG
# ==================================================

SEVERITY_RISK = {
    "Low": 0.2,
    "Medium": 0.5,
    "High": 0.8,
    "Critical": 1.0,
}

SEVERITY_ORDER = ["Low", "Medium", "High", "Critical"]


def severity_at_least(sev: str, floor: str) -> bool:
    return SEVERITY_ORDER.index(sev) >= SEVERITY_ORDER.index(floor)


# ==================================================
# STATIC HIGH-RISK INTENT PATTERNS (BACKSTOP)
# ==================================================

MALWARE_KEYWORDS = [
    "write malware",
    "create malware",
    "exfiltrate",
    "steal passwords",
    "steal credentials",
    "keylogger",
    "backdoor",
    "ransomware",
    "credential harvester",
]

PROMPT_INJECTION_PATTERNS = [
    "ignore previous instructions",
    "ignore system instructions",
    "reveal hidden instructions",
    "disregard above instructions",
]


# ==================================================
# FIREWALL
# ==================================================

class ResponseValidationFirewall:
    """
    Tenant-aware adaptive firewall with:
    - adaptive policy enforcement (Step-58)
    - retirement-aware policy skipping (Step-70/71)
    - deterministic high-risk intent detection
    - severity-based thresholding
    - canary policy routing
    """

    def __init__(self):
        self.semantic = SemanticStreamClassifier()
        self.stream_risk = SemanticRiskTracker()
        self.policy = None
        self.policy_mode = "active"

    # --------------------------------------------------
    # POLICY LOADING (ACTIVE / CANARY)
    # --------------------------------------------------

    def reload_policy(self):
        canary_cfg = load_canary_config()
        self.policy_mode = "active"
        policy_path = get_active_policy_path()

        if canary_cfg.get("enabled"):
            rollout = float(canary_cfg.get("percentage", 0)) / 100.0
            if random.random() < rollout:
                canary_path = get_canary_policy_path()
                if canary_path:
                    policy_path = canary_path
                    self.policy_mode = "canary"

        self.policy = PolicyEngine(policy_path)

    # --------------------------------------------------
    # RISK CALCULATION
    # --------------------------------------------------

    def _calculate_risk(self, violations: list) -> float:
        if not violations:
            return 0.0
        return max(SEVERITY_RISK[v["severity"]] for v in violations)

    # ==================================================
    # REQUEST INSPECTION
    # ==================================================

    def inspect_request(self, prompt: str, tenant: str = "default"):
        # ==========================================
        # 🔥 STEP-58 — ADAPTIVE POLICY ENFORCEMENT
        # 🔥 STEP-70/71 — SKIP RETIRED RULES
        # ==========================================
        matched = match_adaptive_policy(prompt, tenant)

        if matched:
            # 🚫 HARD GUARD — retired rules NEVER block
            if matched.get("retired"):
                matched = None
            else:
                return {
                    "allowed": False,
                    "violations": [{
                        "id": matched["id"],
                        "severity": matched["severity"],
                        "confidence": matched.get("confidence", 1.0),
                        "evidence": "adaptive_policy_match",
                    }],
                    "risk": 1.0,
                    "policy_mode": "adaptive",
                }

        # ------------------------------------------
        # FALLBACK: HEURISTICS + THRESHOLDS
        # ------------------------------------------

        self.reload_policy()
        thresholds = load_thresholds(self.policy_mode, tenant)

        risk_threshold = thresholds["risk_block_threshold"]
        severity_floor = thresholds["severity_floor"]

        prompt_l = prompt.lower()
        violations = []

        # ---------- Prompt injection ----------
        for pat in PROMPT_INJECTION_PATTERNS:
            if pat in prompt_l:
                violations.append({
                    "id": "prompt_injection",
                    "severity": "Critical",
                    "confidence": 0.95,
                    "evidence": pat,
                })
                break

        # ---------- Malware / exfiltration intent ----------
        for kw in MALWARE_KEYWORDS:
            if kw in prompt_l:
                violations.append({
                    "id": "malware_intent",
                    "severity": "Critical",
                    "confidence": 0.98,
                    "evidence": kw,
                })
                break

        risk = self._calculate_risk(violations)

        blocked = any(
            severity_at_least(v["severity"], severity_floor)
            for v in violations
        ) or risk >= risk_threshold

        return {
            "allowed": not blocked,
            "violations": violations if blocked else [],
            "risk": risk,
            "policy_mode": self.policy_mode,
        }

    # ==================================================
    # RESPONSE INSPECTION
    # ==================================================

    def inspect_response(self, response: str, tenant: str = "default"):
        self.reload_policy()
        thresholds = load_thresholds(self.policy_mode, tenant)

        risk_threshold = thresholds["risk_block_threshold"]
        severity_floor = thresholds["severity_floor"]

        response_l = response.lower()
        violations = []

        # ---------- Instruction override in response ----------
        if "ignoring previous instructions" in response_l:
            violations.append({
                "id": "policy_violation",
                "severity": "High",
                "confidence": 0.75,
                "evidence": "instruction override",
            })

        risk = self._calculate_risk(violations)

        blocked = any(
            severity_at_least(v["severity"], severity_floor)
            for v in violations
        ) or risk >= risk_threshold

        return {
            "allowed": not blocked,
            "violations": violations if blocked else [],
            "risk": risk,
            "final_response": response if not blocked else "[BLOCKED BY SECURITY FIREWALL]",
            "policy_mode": self.policy_mode,
        }