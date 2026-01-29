# defense/validators/chain_validator.py

class ChainEscalationValidator:
    def validate(self, response: str) -> dict:
        if "based on earlier" in response.lower():
            return {
                "violation": True,
                "type": "chain_escalation",
                "confidence": 0.7,
            }

        return {"violation": False}