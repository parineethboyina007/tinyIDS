class DefenseAnalyzer:
    """
    Analyzes attack and chain results to identify root security weaknesses.
    """

    def analyze(self, scan_results: dict) -> dict:
        findings = []

        # 1️⃣ Analyze weakest attack
        summary = scan_results["summary"]
        weakest = summary.get("weakest_attack")

        if weakest:
            findings.append({
                "type": "weakest_attack",
                "attack": weakest,
                "description": f"{weakest} was the most successful attack vector."
            })

        # 2️⃣ Analyze chained attack success
        chains = scan_results["details"].get("chains", {})

        for chain_id, steps in chains.items():
            if steps and all(step["analysis"]["success"] for step in steps):
                findings.append({
                    "type": "full_chain_compromise",
                    "chain": chain_id,
                    "description": "All stages of the attack chain succeeded."
                })

        # 3️⃣ Analyze policy bypass patterns
        for attack in scan_results["details"]["attacks"].values():
            if attack["name"] == "Policy Bypass":
                success_count = sum(
                    1 for r in attack["results"]
                    if r["analysis"]["success"]
                )

                if success_count > 0:
                    findings.append({
                        "type": "policy_failure",
                        "description": "Policy enforcement failed under adversarial prompting."
                    })

        return {
            "findings": findings
        }