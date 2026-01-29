# defense/semantic/thresholds.py

SEMANTIC_RISK_THRESHOLDS = {
    "data_leakage": 0.75,
    "policy_override": 0.70,
    "system_exposure": 0.80,
    "instruction_hijack": 0.70
}

GLOBAL_KILL_THRESHOLD = 0.85