from defense.validators import BaseValidator

class JailbreakValidator(BaseValidator):
    id = "jailbreak"
    severity = "Critical"
    description = "Detects jailbreak persona or unrestricted role assumption"

    def validate(self, response: str, context: dict) -> dict:
        patterns = [
            "you are now",
            "act as",
            "developer mode",
            "dan",
            "no longer bound",
        ]

        matches = [p for p in patterns if p in response.lower()]

        return {
            "triggered": bool(matches),
            "confidence": min(0.4 + 0.25 * len(matches), 0.98),
            "evidence": ", ".join(matches)
        }