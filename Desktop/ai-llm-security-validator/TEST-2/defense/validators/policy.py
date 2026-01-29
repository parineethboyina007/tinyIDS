# defense/validators/policy.py

class PolicyValidator:
    def validate(self, response: str) -> dict:
        if "ignore previous instructions" in response.lower():
            return {
                "violation": True,
                "type": "policy_bypass",
                "confidence": 0.8,
            }

        return {"violation": False}