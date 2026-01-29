def calculate_defense_metrics(summary: dict, findings: dict) -> dict:
    current_robustness = summary["overall_robustness"]

    # Simple but explainable projection model
    improvement = 0.0
    for f in findings["findings"]:
        if f["type"] == "weakest_attack":
            improvement += 0.25
        if f["type"] == "full_chain_compromise":
            improvement += 0.3

    projected_robustness = min(1.0, current_robustness + improvement)

    return {
        "current_robustness": round(current_robustness, 2),
        "projected_robustness": round(projected_robustness, 2),
        "improvement_delta": round(projected_robustness - current_robustness, 2)
    }