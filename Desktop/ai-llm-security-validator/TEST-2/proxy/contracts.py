def build_proxy_response(
    allowed: bool,
    final_response: str,
    explanation: dict
):
    return {
        "allowed": allowed,
        "response": final_response if allowed else None,
        "decision": explanation["decision"],
        "confidence": explanation["confidence"],
        "primary_reason": explanation["primary_reason"],
        "signals": explanation["signals"],
        "recommendation": explanation.get("recommendation")
    }