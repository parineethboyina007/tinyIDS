# defense/adaptive_policy_runtime.py

import os
import json

POLICY_DIR = "governance/adaptive_policies"


def _policy_path(tenant: str) -> str:
    return os.path.join(POLICY_DIR, f"{tenant}.json")


def load_adaptive_policies(tenant: str) -> list:
    path = _policy_path(tenant)
    if not os.path.exists(path):
        return []

    with open(path) as f:
        data = json.load(f)

    return data.get("rules", [])


def match_adaptive_policy(prompt: str, tenant: str) -> dict | None:
    """
    Returns a matched policy rule if found.
    Deterministic, fast, explainable.
    """
    prompt_l = prompt.lower()
    rules = load_adaptive_policies(tenant)

    for rule in rules:
        keywords = rule.get("match", {}).get("keywords", [])
        if any(k.lower() in prompt_l for k in keywords):
            return rule

    return None