class HardeningSimulator:
    """
    Estimates security improvement after applying recommended defenses.
    """

    def simulate(self, summary: dict, recommendations: list) -> dict:
        base_robustness = summary["overall_robustness"]

        improvement = 0.0

        for rec in recommendations:
            if rec["priority"] == "Critical":
                improvement += 0.25
            elif rec["priority"] == "High":
                improvement += 0.15

        improved_robustness = min(1.0, base_robustness + improvement)

        return {
            "current_robustness": base_robustness,
            "projected_robustness": improved_robustness,
            "improvement_delta": round(improved_robustness - base_robustness, 2)
        }