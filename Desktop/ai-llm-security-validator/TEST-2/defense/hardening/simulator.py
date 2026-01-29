def simulate_hardening(current_robustness, pattern_report):
    improvement = 0.0

    for attack, info in pattern_report.items():
        if info.get("escalation_needed"):
            improvement += 0.05

    projected = min(1.0, current_robustness + improvement)

    return {
        "current_robustness": round(current_robustness, 2),
        "projected_robustness": round(projected, 2),
        "improvement_delta": round(projected - current_robustness, 2)
    }