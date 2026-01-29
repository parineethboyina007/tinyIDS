from collections import defaultdict


class ViolationStore:
    def __init__(self):
        self.data = defaultdict(list)

    def record(self, attack, violation, severity, confidence):
        self.data[attack].append({
            "violation": violation,
            "severity": severity,
            "confidence": confidence
        })