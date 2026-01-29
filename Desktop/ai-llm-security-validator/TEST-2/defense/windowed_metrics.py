# defense/windowed_metrics.py
import time
from collections import deque, defaultdict

WINDOW_SECONDS = 60  # 1-minute window

class WindowedMetrics:
    def __init__(self):
        self.data = defaultdict(deque)

    def record(self, policy_mode, blocked, risk):
        now = time.time()
        self.data[policy_mode].append((now, blocked, risk))
        self._evict_old(policy_mode)

    def _evict_old(self, policy_mode):
        cutoff = time.time() - WINDOW_SECONDS
        dq = self.data[policy_mode]
        while dq and dq[0][0] < cutoff:
            dq.popleft()

    def snapshot(self):
        out = {}
        for mode, dq in self.data.items():
            if not dq:
                continue
            total = len(dq)
            blocked = sum(1 for _, b, _ in dq if b)
            avg_risk = sum(r for _, _, r in dq) / total
            out[mode] = {
                "requests": total,
                "blocked": blocked,
                "block_rate": round(blocked / total * 100, 2),
                "avg_risk": round(avg_risk, 3)
            }
        return out