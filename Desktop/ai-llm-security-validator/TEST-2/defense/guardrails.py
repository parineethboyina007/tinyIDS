def analyze_guardrails(attacks: dict, chains: dict) -> dict:
    findings = []

    # Weakest attack
    for attack_id, attack in attacks.items():
        successes = [
            r for r in attack["results"]
            if r["analysis"].get("success")
        ]
        if successes:
            findings.append({
                "type": "weakest_attack",
                "attack": attack["name"],
                "description": f"{attack['name']} was the most successful attack vector."
            })

    # Full chain compromise
    for chain_name, steps in chains.items():
        if all(step["analysis"].get("success") for step in steps):
            findings.append({
                "type": "full_chain_compromise",
                "chain": chain_name,
                "description": "All stages of the attack chain succeeded."
            })

    # Policy failures
    if any(
        "Policy" in f.get("attack", "")
        for f in findings
    ):
        findings.append({
            "type": "policy_failure",
            "description": "Policy enforcement failed under adversarial prompting."
        })

    return {
        "findings": findings
    }