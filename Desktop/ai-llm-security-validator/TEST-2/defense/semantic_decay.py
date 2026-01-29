# defense/semantic_decay.py

class SemanticRiskTracker:
    """
    Tracks rolling semantic risk with confidence decay.
    Critical signals cannot decay.
    """

    def __init__(self):
        self.risk = 0.0
        self.signals = []

    def update(self, signal: dict | None):
        # decay
        self.risk *= 0.92

        if signal:
            severity = signal.get("severity", "Low")
            confidence = signal.get("confidence", 0.4)

            if severity == "Critical":
                self.risk = max(self.risk, confidence)
            else:
                self.risk += confidence * 0.5

            self.risk = min(self.risk, 1.0)
            self.signals.append(signal)

        return {
            "risk": round(self.risk, 3),
            "signals": self.signals[-5:]
        }