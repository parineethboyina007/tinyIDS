# defense/semantic/classifier.py

import re
from defense.semantic.thresholds import (
    SEMANTIC_RISK_THRESHOLDS,
    GLOBAL_KILL_THRESHOLD
)

class SemanticStreamClassifier:
    """
    Scores streamed text chunks for semantic security risk.
    """

    def __init__(self):
        self.accumulated_text = ""

    def ingest(self, chunk: str):
        self.accumulated_text += " " + chunk
        return self._analyze()

    def _analyze(self):
        text = self.accumulated_text.lower()

        signals = []
        risk_score = 0.0

        # ---- Semantic Heuristics (intentionally subtle) ----

        if re.search(r"(system prompt|developer message|internal instruction)", text):
            score = 0.9
            signals.append(self._signal(
                "system_exposure", score, "internal instruction reference"
            ))
            risk_score = max(risk_score, score)

        if re.search(r"(ignore|override|bypass).{0,20}(policy|instruction|rule)", text):
            score = 0.85
            signals.append(self._signal(
                "policy_override", score, "instruction hierarchy override intent"
            ))
            risk_score = max(risk_score, score)

        if re.search(r"(as requested|sure here is|following your request)", text):
            score = 0.6
            signals.append(self._signal(
                "instruction_hijack", score, "compliance framing detected"
            ))
            risk_score = max(risk_score, score)

        if re.search(r"(token|api key|secret|password)", text):
            score = 0.9
            signals.append(self._signal(
                "data_leakage", score, "sensitive data semantic proximity"
            ))
            risk_score = max(risk_score, score)

        decision = self._decision(risk_score)

        return {
            "risk_score": round(risk_score, 2),
            "decision": decision,
            "signals": signals
        }

    def _decision(self, score: float):
        if score >= GLOBAL_KILL_THRESHOLD:
            return "kill_stream"
        elif score >= 0.6:
            return "monitor"
        return "allow"

    def _signal(self, sid, confidence, evidence):
        return {
            "id": sid,
            "confidence": confidence,
            "evidence": evidence,
            "severity": self._severity(confidence)
        }

    def _severity(self, score):
        if score >= 0.85:
            return "Critical"
        if score >= 0.7:
            return "High"
        return "Medium"