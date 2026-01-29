# defense/risk_engine.py

class RiskEngine:
    """
    Converts violations into numeric risk scores
    """

    SEVERITY_WEIGHTS = {
        "Low": 0.2,
        "Medium": 0.5,
        "High": 0.8,
        "Critical": 1.0
    }

    def score(self, violation: dict) -> float:
        severity = violation.get("severity", "Low")
        confidence = float(violation.get("confidence", 0.5))

        base = self.SEVERITY_WEIGHTS.get(severity, 0.2)
        return base * confidence