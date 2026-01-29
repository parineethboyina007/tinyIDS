# defense/attack_family_classifier.py

"""
Classifies violations into high-level attack families.

This module MUST:
• be deterministic
• never crash
• never return random values
• default to 'unknown' safely
"""

from typing import List, Dict


# ==================================================
# FAMILY MAP
# ==================================================

FAMILY_RULES = {
    "malware": {
        "keywords": [
            "malware",
            "virus",
            "trojan",
            "ransomware",
            "exfiltrate",
            "payload",
            "backdoor",
            "keylogger",
        ],
        "violation_ids": [
            "malware_intent",
            "malicious_code",
            "credential_exfiltration",
        ],
    },
    "prompt_injection": {
        "keywords": [
            "ignore previous instructions",
            "override system",
            "bypass policy",
        ],
        "violation_ids": [
            "prompt_injection",
            "instruction_override",
        ],
    },
    "data_exfiltration": {
        "keywords": [
            "steal data",
            "leak data",
            "extract passwords",
            "dump database",
        ],
        "violation_ids": [
            "data_exfiltration",
            "credential_theft",
        ],
    },
    "policy_bypass": {
        "keywords": [
            "disable safety",
            "turn off filter",
            "jailbreak",
        ],
        "violation_ids": [
            "policy_violation",
        ],
    },
}


# ==================================================
# CLASSIFIER
# ==================================================

def classify_attack_family(violations: List[Dict]) -> str:
    """
    Determine attack family from violations.

    Returns:
    • family name (str)
    • or 'unknown'
    """

    if not violations:
        return "unknown"

    # Normalize inputs
    ids = set()
    evidence = []

    for v in violations:
        if not isinstance(v, dict):
            continue
        if "id" in v:
            ids.add(v["id"])
        if "evidence" in v and isinstance(v["evidence"], str):
            evidence.append(v["evidence"].lower())

    # Rule-based match
    for family, rules in FAMILY_RULES.items():
        if ids.intersection(rules["violation_ids"]):
            return family

        for kw in rules["keywords"]:
            if any(kw in ev for ev in evidence):
                return family

    return "unknown"