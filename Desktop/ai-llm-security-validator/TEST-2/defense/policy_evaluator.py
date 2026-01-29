# defense/policy_evaluator.py

def should_promote(canary: dict, active: dict) -> bool:
    """
    Decide if canary policy is safe to promote
    """

    MIN_REQUESTS = 100
    BLOCK_TOLERANCE = 5.0  # %

    if canary["requests"] < MIN_REQUESTS:
        return False

    if canary["block_rate"] > active["block_rate"] + BLOCK_TOLERANCE:
        return False

    if canary["avg_risk"] > active["avg_risk"]:
        return False

    return True