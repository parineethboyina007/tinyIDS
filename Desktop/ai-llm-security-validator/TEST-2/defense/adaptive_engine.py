from defense.learning.violation_store import ViolationStore
from defense.learning.attack_patterns import AttackPatternAnalyzer
from defense.learning.thresholds import AdaptiveThresholds
from defense.hardening.simulator import simulate_hardening


class AdaptiveDefenseEngine:
    def __init__(self):
        self.store = ViolationStore()
        self.patterns = AttackPatternAnalyzer()
        self.thresholds = AdaptiveThresholds()

    def process(self, scan_result: dict):
        attacks = scan_result["details"]["attacks"]
        history = scan_result["details"]["history"]
        summary = scan_result["summary"]

        # 1️⃣ Learn from firewall violations
        for entry in history:
            firewall = entry["analysis"].get("firewall")
            if firewall and not firewall["allowed"]:
                for v in firewall["violations"]:
                    self.store.record(
                        attack=entry["attack"],
                        violation=v["id"],
                        severity=v["severity"],
                        confidence=v["confidence"]
                    )

        # 2️⃣ Analyze patterns
        pattern_report = self.patterns.analyze(self.store.data)

        # 3️⃣ Adapt thresholds
        self.thresholds.update(pattern_report)

        # 4️⃣ Simulate hardening
        hardening_simulation = simulate_hardening(
            current_robustness=summary["overall_robustness"],
            pattern_report=pattern_report
        )

        return {
            "patterns": pattern_report,
            "thresholds": self.thresholds.export(),
            "hardening_simulation": hardening_simulation
        }