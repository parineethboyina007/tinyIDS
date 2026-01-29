# defense/request_explainability_store.py

import os
import json
from datetime import datetime

STORE_DIR = "governance/request_explanations"
os.makedirs(STORE_DIR, exist_ok=True)


def _path(request_id: str) -> str:
    return os.path.join(STORE_DIR, f"{request_id}.json")


def save_request_explanation(request_id: str, data: dict):
    payload = {
        "request_id": request_id,
        "data": data,
        "stored_at": datetime.utcnow().isoformat(),
    }
    with open(_path(request_id), "w") as f:
        json.dump(payload, f, indent=2)


def load_request_explanation(request_id: str):
    path = _path(request_id)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)