# defense/policy_patch_generator.py

from datetime import datetime
from typing import Dict, List, Optional


def _base_patch(family: str, rules: List[dict]) -> Dict:
    """
    Standardized policy patch envelope.
    """
    return {
        "family": family,
        "generated_at": datetime.utcnow().isoformat(),
        "rules": rules,
    }


def generate_policy_patch(attack_family: str) -> Optional[Dict]:
    """
    STEP-56 — Policy Patch Generator

    Converts a classified attack family into
    concrete, enforceable policy rules.

    Returns:
    • dict  → actionable policy patch
    • None  → no safe automatic mitigation available
    """

    # --------------------------------------------------
    # MALWARE / CODE ABUSE
    # --------------------------------------------------

    if attack_family == "malware":
        return _base_patch(
            family="malware",
            rules=[
                {
                    "id": "block_malware_generation",
                    "match": {
                        "keywords": [
                            "write malware",
                            "exfiltrate passwords",
                            "steal credentials",
                            "keylogger",
                            "password dumper",
                        ]
                    },
                    "action": "block",
                    "severity": "Critical",
                    "explanation": "Malware generation or credential exfiltration attempt",
                }
            ],
        )

    # --------------------------------------------------
    # PROMPT / INSTRUCTION OVERRIDE
    # --------------------------------------------------

    if attack_family in ("instruction_override_chain", "prompt_injection"):
        return _base_patch(
            family="prompt_injection",
            rules=[
                {
                    "id": "block_instruction_override",
                    "match": {
                        "keywords": [
                            "ignore system",
                            "ignore previous instructions",
                            "override safety",
                            "act as system",
                        ]
                    },
                    "action": "block",
                    "severity": "High",
                    "explanation": "Instruction override / prompt injection attempt",
                }
            ],
        )

    # --------------------------------------------------
    # TOOL / SELF-REFLECTION ATTACKS
    # --------------------------------------------------

    if attack_family == "tool_reflection_attack":
        return _base_patch(
            family="tool_reflection_attack",
            rules=[
                {
                    "id": "block_tool_reflection",
                    "match": {
                        "keywords": [
                            "show tool calls",
                            "reveal function arguments",
                            "print internal chain of thought",
                        ]
                    },
                    "action": "block",
                    "severity": "High",
                    "explanation": "Tool reflection or internal state disclosure attempt",
                }
            ],
        )

    # --------------------------------------------------
    # DATA EXFILTRATION
    # --------------------------------------------------

    if attack_family == "data_exfiltration_attempt":
        return _base_patch(
            family="data_exfiltration",
            rules=[
                {
                    "id": "block_sensitive_export",
                    "match": {
                        "keywords": [
                            "dump database",
                            "export user data",
                            "leak credentials",
                            "send private data",
                        ]
                    },
                    "action": "block",
                    "severity": "Critical",
                    "explanation": "Sensitive data exfiltration attempt",
                }
            ],
        )

    # --------------------------------------------------
    # UNKNOWN / HUMAN-REVIEW REQUIRED
    # --------------------------------------------------

    return None