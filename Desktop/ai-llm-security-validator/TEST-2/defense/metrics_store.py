# defense/metrics_store.py

from collections import defaultdict
from threading import Lock

_lock = Lock()

_total = defaultdict(lambda: {
    "requests": 0,
    "blocked": 0,
    "total_risk": 0.0,
})

_window = defaultdict(lambda: {
    "requests": 0,
    "blocked": 0,
    "total_risk": 0.0,
})

def record(policy_mode: str, blocked: bool, risk: float = 0.0):
    with _lock:
        for store in (_total, _window):
            m = store[policy_mode]
            m["requests"] += 1
            if blocked:
                m["blocked"] += 1
            m["total_risk"] += risk

def snapshot():
    def build(src):
        out = {}
        for mode, m in src.items():
            r = m["requests"]
            out[mode] = {
                "requests": r,
                "blocked": m["blocked"],
                "block_rate": round((m["blocked"] / r) * 100, 2) if r else 0.0,
                "avg_risk": round(m["total_risk"] / r, 3) if r else 0.0,
            }
        return out

    with _lock:
        return {
            "windowed": build(_window),
            "total": build(_total),
        }

def reset():
    with _lock:
        _window.clear()
        _total.clear()