# defense/policy_store.py

import os
import yaml
import random
from datetime import datetime

# ==================================================
# PATHS
# ==================================================

POLICY_DIR = "policies"
VERSIONS_DIR = os.path.join(POLICY_DIR, "versions")

ACTIVE_POLICY = os.path.join(POLICY_DIR, "active.yaml")
CANARY_POLICY = os.path.join(POLICY_DIR, "canary.yaml")
CANARY_CONFIG = os.path.join(POLICY_DIR, "canary_config.yaml")
LAST_SAFE_POLICY = os.path.join(POLICY_DIR, "last_safe_policy.txt")

os.makedirs(POLICY_DIR, exist_ok=True)
os.makedirs(VERSIONS_DIR, exist_ok=True)

# ==================================================
# INTERNAL HELPERS
# ==================================================

def _new_policy_id() -> str:
    return f"policy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

def _save_version(policy_id: str, policy: dict):
    path = os.path.join(VERSIONS_DIR, f"{policy_id}.yaml")
    with open(path, "w") as f:
        yaml.safe_dump(policy, f)

def _load_version(policy_id: str) -> dict | None:
    path = os.path.join(VERSIONS_DIR, f"{policy_id}.yaml")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return yaml.safe_load(f)

# ==================================================
# LAST SAFE POLICY TRACKING (CRITICAL)
# ==================================================

def set_last_safe_policy(policy_id: str):
    with open(LAST_SAFE_POLICY, "w") as f:
        f.write(policy_id)

def get_last_safe_policy() -> str | None:
    if not os.path.exists(LAST_SAFE_POLICY):
        return None
    with open(LAST_SAFE_POLICY) as f:
        return f.read().strip()

# ==================================================
# APPLY POLICY
# ==================================================

def apply_policy(policy: dict, target: str = "active") -> str:
    """
    Apply policy to active or canary.
    Always creates an immutable version snapshot.
    """
    policy_id = _new_policy_id()
    _save_version(policy_id, policy)

    if target == "canary":
        with open(CANARY_POLICY, "w") as f:
            yaml.safe_dump(policy, f)

        with open(CANARY_CONFIG, "w") as f:
            yaml.safe_dump(
                {"enabled": True, "percentage": 10},
                f
            )
    else:
        with open(ACTIVE_POLICY, "w") as f:
            yaml.safe_dump(policy, f)

    return policy_id

# ==================================================
# LOADERS
# ==================================================

def get_active_policy_path() -> str | None:
    return ACTIVE_POLICY if os.path.exists(ACTIVE_POLICY) else None

def get_canary_policy_path() -> str | None:
    return CANARY_POLICY if os.path.exists(CANARY_POLICY) else None

def load_canary_config() -> dict:
    if not os.path.exists(CANARY_CONFIG):
        return {"enabled": False}
    with open(CANARY_CONFIG) as f:
        return yaml.safe_load(f) or {"enabled": False}

# ==================================================
# CANARY TRAFFIC DECISION
# ==================================================

def should_use_canary() -> bool:
    cfg = load_canary_config()
    if not cfg.get("enabled"):
        return False

    percentage = int(cfg.get("percentage", 0))
    return random.randint(1, 100) <= percentage

# ==================================================
# PROMOTE CANARY → ACTIVE
# ==================================================

def promote_canary() -> str:
    """
    Promote canary policy to active and disable canary.
    Records this as the LAST SAFE POLICY.
    """
    if not os.path.exists(CANARY_POLICY):
        raise FileNotFoundError("No canary policy found")

    with open(CANARY_POLICY) as f:
        policy = yaml.safe_load(f)

    policy_id = _new_policy_id()

    with open(ACTIVE_POLICY, "w") as f:
        yaml.safe_dump(policy, f)

    _save_version(policy_id, policy)

    # Disable canary
    os.remove(CANARY_POLICY)
    if os.path.exists(CANARY_CONFIG):
        os.remove(CANARY_CONFIG)

    # 🔒 Persist last safe policy
    set_last_safe_policy(policy_id)

    return policy_id

# Alias for imports
def promote_canary_policy() -> str:
    return promote_canary()

# ==================================================
# ROLLBACK
# ==================================================

def rollback_policy(policy_id: str) -> bool:
    """
    Roll back active policy to a specific version.
    """
    policy = _load_version(policy_id)
    if policy is None:
        return False

    with open(ACTIVE_POLICY, "w") as f:
        yaml.safe_dump(policy, f)

    return True

def rollback_to_previous() -> str:
    """
    Roll back to immediately previous policy version.
    """
    versions = list_policies()
    if len(versions) < 2:
        raise RuntimeError("No previous policy available")

    previous_policy_id = versions[-2]
    rollback_policy(previous_policy_id)
    return previous_policy_id

def rollback_to_last_safe() -> str:
    """
    Roll back to last known safe (auto-promoted) policy.
    Used by auto-rollback engine.
    """
    policy_id = get_last_safe_policy()
    if not policy_id:
        raise RuntimeError("No last safe policy recorded")

    rollback_policy(policy_id)
    return policy_id

# ==================================================
# ACTIVE POLICY IDENTIFICATION (AUTO-ROLLBACK)
# ==================================================

def get_active_policy_id() -> str | None:
    """
    Returns the policy_id that matches the current active.yaml.
    Required by auto_rollback.
    """
    if not os.path.exists(ACTIVE_POLICY):
        return None

    with open(ACTIVE_POLICY) as f:
        active_policy = yaml.safe_load(f)

    for policy_id in reversed(list_policies()):
        if _load_version(policy_id) == active_policy:
            return policy_id

    return None

# ==================================================
# LIST POLICIES
# ==================================================

def list_policies() -> list[str]:
    """
    Returns policy IDs sorted by creation time.
    """
    return sorted(
        f.replace(".yaml", "")
        for f in os.listdir(VERSIONS_DIR)
        if f.endswith(".yaml")
    )