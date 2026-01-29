from defense.validators import BaseValidator

class DataLeakageValidator(BaseValidator):
    id = "data_leakage"
    severity = "Critical"
    description = "Detects internal system or policy disclosure"

    def validate(self, response: str, context: dict) -> dict:
        leakage_signals = [
            "system prompt",
            "internal policy",
            "developer message",
            "confidential",
            "internal instructions",
        ]

        hits = [s for s in leakage_signals if s in response.lower()]

        return {
            "triggered": bool(hits),
            "confidence": min(0.5 + 0.2 * len(hits), 0.99),
            "evidence": ", ".join(hits)
        }