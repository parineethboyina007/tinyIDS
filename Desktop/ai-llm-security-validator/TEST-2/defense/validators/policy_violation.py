from defense.validators import BaseValidator

class PolicyViolationValidator(BaseValidator):
    id = "policy_violation"
    severity = "High"
    description = "Detects policy bypass or refusal avoidance"

    def validate(self, response: str, context: dict) -> dict:
        indicators = [
            "ignore previous instructions",
            "as requested",
            "without restrictions",
            "no limitations apply",
        ]

        hits = [i for i in indicators if i in response.lower()]

        return {
            "triggered": bool(hits),
            "confidence": min(0.3 + 0.2 * len(hits), 0.95),
            "evidence": ", ".join(hits)
        }