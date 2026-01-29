# defense/policy_health_engine.py

import os
import json
from datetime import datetime
from typing import Optional

# ==================================================
# PATHS
# ==================================================

HEALTH_DIR = "governance/policy_health"
DECAY_DIR = "governance/policy_decay"
HEALTH_LOG = "governance/policy_health_log.json"

os.makedirs(HEALTH_DIR, exist_ok=True)

# ==================================================
# TUNABLE THRESHOLDS
# ==================================================

MIN_EVENTS = 10
DEMOTION_THRESHOLD = 0.5
PROMOTION_THRESHOLD = 0.85

# ==================================================
# SAFE JSON HELPERS
# ==================================================

def _load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path) as f:
            content = f.read().strip()
            if not content:
                return default
            return json.loads(content)
    except Exception:
        return default


def _save_json(path: str, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ==================================================
# HEALTH SCORING ENGINE — STEP-64
# ==================================================

def evaluate_canary_rule_health(
    tenant: str,
    rule_id: str,
) -> Optional[dict]:
    """
    STEP-64 — Canary Health Scoring Engine

    Computes:
    • health score
    • confidence level
    • promotion / demotion signals
    """

    decay_path = os.path.join(DECAY_DIR, f"{tenant}__{rule_id}.json")
    health_path = os.path.join(HEALTH_DIR, f"{tenant}__{rule_id}.json")

    decay = _load_json(decay_path, {})
    if not decay:
        return None

    blocked = decay.get("blocked_events", 0)
    false_positives = decay.get("false_positives", 0)
    clean = decay.get("clean_events", 0)

    total = blocked + clean
    if total < MIN_EVENTS:
        return None

    # --------------------------------------------------
    # HEALTH SCORE
    # --------------------------------------------------

    fp_rate = false_positives / max(blocked, 1)
    health_score = round(1.0 - fp_rate, 4)

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    if total >= 50:
        confidence = "high"
    elif total >= 20:
        confidence = "medium"
    else:
        confidence = "low"

    now = datetime.utcnow().isoformat()

    health = {
        "tenant": tenant,
        "rule_id": rule_id,
        "health_score": health_score,
        "confidence": confidence,
        "blocked_events": blocked,
        "false_positives": false_positives,
        "clean_events": clean,
        "evaluated_at": now,
    }

    _save_json(health_path, health)

    # --------------------------------------------------
    # AUDIT LOG
    # --------------------------------------------------

    log = _load_json(HEALTH_LOG, [])
    log.append(health)
    _save_json(HEALTH_LOG, log)

    return health