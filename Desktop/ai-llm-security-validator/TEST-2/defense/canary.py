import random
from defense.policy_store import load_canary_config


def use_canary_policy() -> bool:
    cfg = load_canary_config()
    if not cfg.get("enabled"):
        return False

    pct = cfg.get("percentage", 0)
    return random.randint(1, 100) <= pct