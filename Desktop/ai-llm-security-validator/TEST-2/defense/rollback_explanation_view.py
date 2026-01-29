# defense/rollback_explanation_view.py

def build_ui_view(explanation: dict) -> dict:
    metrics = explanation["metrics"]
    current = explanation["current_thresholds"]
    recommended = explanation["recommended_thresholds"]

    # Severity badge
    severity = current["severity_floor"]
    if severity == "Critical":
        badge = "red"
    elif severity == "High":
        badge = "orange"
    elif severity == "Medium":
        badge = "yellow"
    else:
        badge = "green"

    # Human summary
    summary = (
        f"System entered saturation with {metrics['block_rate']}% blocks "
        f"and sustained high risk. Current thresholds reached maximum safety. "
        f"A rollback to safer operational thresholds is recommended."
    )

    return {
        "id": explanation["_id"],
        "tenant": explanation["tenant"],
        "mode": explanation["mode"],
        "trigger": explanation["trigger"],
        "severity_badge": badge,
        "summary": summary,
        "metrics": metrics,
        "current_thresholds": current,
        "recommended_thresholds": recommended,
        "why": explanation["decision"]["why"],
        "safety_notes": explanation["safety_notes"],
        "generated_at": explanation["generated_at"],
    }