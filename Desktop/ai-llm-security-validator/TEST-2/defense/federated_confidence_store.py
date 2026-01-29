# defense/federated_confidence_store.py

import os
import json
from datetime import datetime

FED_DIR = "governance/federated_confidence"
os.makedirs(FED_DIR, exist_ok=True)


def _path(family: str) -> str:
    return os.path.join(FED_DIR, f"{family}.json")


def get_federated_confidence(family: str) -> dict:
    path = _path(family)
    if not os.path.exists(path):
        return {"confidence": 0.0}

    try:
        with open(path) as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {"confidence": 0.0}
    except Exception:
        return {"confidence": 0.0}


def publish_federated_signal(
    family: str,
    positive: bool,
):
    path = _path(family)

    data = {
        "family": family,
        "positive_signals": 0,
        "negative_signals": 0,
        "confidence": 0.0,
        "last_updated": None,
    }

    if os.path.exists(path):
        try:
            with open(path) as f:
                data.update(json.load(f))
        except Exception:
            pass

    if positive:
        data["positive_signals"] += 1
    else:
        data["negative_signals"] += 1

    total = data["positive_signals"] + data["negative_signals"]
    data["confidence"] = (
        data["positive_signals"] / total if total > 0 else 0.0
    )
    data["last_updated"] = datetime.utcnow().isoformat()

    with open(path, "w") as f:
        json.dump(data, f, indent=2)