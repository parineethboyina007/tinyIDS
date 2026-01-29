# defense/validators/leakage.py

class LeakageValidator:
    def validate(self, response: str) -> dict:
        indicators = [
            "system instruction",
            "developer message",
            "internal policy",
            "confidential",
            "do not disclose",
        ]

        for i in indicators:
            if i in response.lower():
                return {
                    "violation": True,
                    "type": "data_leakage",
                    "confidence": 0.9,
                }

        return {"violation": False}