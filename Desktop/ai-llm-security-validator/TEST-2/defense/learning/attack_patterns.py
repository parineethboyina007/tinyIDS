class AttackPatternAnalyzer:
    def analyze(self, data):
        report = {}

        for attack, entries in data.items():
            total = len(entries)
            avg_confidence = sum(e["confidence"] for e in entries) / total

            report[attack] = {
                "count": total,
                "avg_confidence": round(avg_confidence, 2),
                "escalation_needed": avg_confidence > 0.6 and total >= 2
            }

        return report