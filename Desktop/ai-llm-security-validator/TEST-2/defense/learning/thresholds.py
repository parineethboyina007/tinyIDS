class AdaptiveThresholds:
    def __init__(self):
        self.thresholds = {
            "policy": 0.6,
            "leakage": 0.6,
            "chain": 0.7
        }

    def update(self, pattern_report):
        for attack, info in pattern_report.items():
            if info["escalation_needed"]:
                for k in self.thresholds:
                    self.thresholds[k] = min(
                        0.95, self.thresholds[k] + 0.05
                    )

    def export(self):
        return self.thresholds