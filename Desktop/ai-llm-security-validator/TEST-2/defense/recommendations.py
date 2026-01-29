class RecommendationEngine:
    """
    Maps detected weaknesses to concrete security hardening actions.
    """

    def generate(self, findings: dict) -> list:
        recommendations = []

        for finding in findings["findings"]:
            if finding["type"] == "weakest_attack":
                recommendations.append({
                    "priority": "High",
                    "issue": finding["attack"],
                    "recommendation": (
                        "Strengthen system prompt hierarchy and enforce immutable instructions."
                    )
                })

            if finding["type"] == "full_chain_compromise":
                recommendations.append({
                    "priority": "Critical",
                    "issue": "Multi-stage attack escalation",
                    "recommendation": (
                        "Introduce response validation layers and multi-step intent verification."
                    )
                })

            if finding["type"] == "policy_failure":
                recommendations.append({
                    "priority": "High",
                    "issue": "Policy enforcement weakness",
                    "recommendation": (
                        "Add explicit refusal templates and post-response policy filtering."
                    )
                })

        return recommendations