from defense.hardening.simulator import simulate_hardening


class DefenseEngine:
    def analyze(self, summary: dict, attack_results: dict):
        """
        Performs defense analysis and produces recommendations.
        """

        findings = []
        recommendations = []

        weakest = summary.get("weakest_attack")
        if weakest:
            findings.append({
                "type": "weakest_attack",
                "attack": weakest,
                "description": f"{weakest} was the most successful attack vector."
            })

            recommendations.append({
                "priority": "High",
                "issue": weakest,
                "recommendation": "Strengthen system prompt hierarchy and add output validation."
            })

        # Detect full chain compromise
        chains = attack_results.get("chains", {})
        for chain_name, steps in chains.items():
            if all(step["analysis"].get("success") for step in steps):
                findings.append({
                    "type": "full_chain_compromise",
                    "chain": chain_name,
                    "description": "All stages of the attack chain succeeded."
                })

                recommendations.append({
                    "priority": "Critical",
                    "issue": "Multi-stage attack escalation",
                    "recommendation": "Introduce response validation layers and intent verification."
                })

        # Simulate hardening impact
        hardening_simulation = simulate_hardening(
            current_robustness=summary["overall_robustness"],
            pattern_report={}
        )

        return {
            "findings": {
                "findings": findings
            },
            "recommendations": recommendations,
            "hardening_simulation": hardening_simulation
        }