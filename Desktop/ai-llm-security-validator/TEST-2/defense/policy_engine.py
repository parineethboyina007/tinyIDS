# defense/policy_engine.py

import json
import os
from typing import List, Dict, Optional

# ==================================================
# POLICY ENGINE
# ==================================================

class PolicyEngine:
    """
    STEP-63 compliant adaptive policy engine.

    Supports:
    • active vs canary policy separation
    • narrowed rules
    • canary-only re-widening
    • safe idempotent evaluation
    """

    def __init__(self, policy_path: Optional[str], policy_mode: str = "active"):
        self.policy_mode = policy_mode
        self.rules: List[Dict] = []

        if policy_path and os.path.exists(policy_path):
            try:
                with open(policy_path) as f:
                    data = json.load(f)
                    self.rules = data.get("rules", [])
            except Exception:
                self.rules = []

    # ==================================================
    # RULE MATCHING
    # ==================================================

    def evaluate(self, text: str) -> List[Dict]:
        """
        Evaluate text against adaptive policies.

        Returns:
        • list of matched violations
        """

        text_l = text.lower()
        violations = []

        for rule in self.rules:
            # ------------------------------------------
            # STEP-62: CANARY-ONLY RE-WIDENING GUARD
            # ------------------------------------------

            if rule.get("rewidening_mode") == "canary":
                if self.policy_mode != "canary":
                    continue  # DO NOT APPLY YET

            # ------------------------------------------
            # NARROWED RULE CONTEXT REQUIREMENT
            # ------------------------------------------

            if rule.get("narrowed"):
                required = rule.get("require_context", [])
                if required:
                    if not any(ctx in text_l for ctx in required):
                        continue

            # ------------------------------------------
            # KEYWORD MATCHING
            # ------------------------------------------

            match = rule.get("match", {})
            keywords = match.get("keywords", [])

            if not keywords:
                continue

            if not any(k.lower() in text_l for k in keywords):
                continue

            # ------------------------------------------
            # VIOLATION EMITTED
            # ------------------------------------------

            violations.append({
                "id": rule.get("id"),
                "severity": rule.get("severity", "Medium"),
                "confidence": rule.get("confidence", 1),
                "evidence": "adaptive_policy_match",
                "family": rule.get("family"),
            })

        return violations