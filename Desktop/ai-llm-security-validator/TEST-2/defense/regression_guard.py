# defense/regression_guard.py

from audit.store import load_event
from replay.executor import ReplayExecutor

# Hard safety rule
MAX_ALLOWED_REGRESSIONS = 0


def run_regression_replay(limit: int = 20):
    """
    Replays previously blocked ACTIVE requests
    against CANARY policy and checks for regressions.
    """

    failures = []

    # Load recent blocked ACTIVE requests
    blocked_events = [
        e for e in load_recent_events(limit=limit)
        if e.get("blocked") is True
        and e.get("policy_mode") == "active"
    ]

    executor = ReplayExecutor(
        provider_name=None,   # reuse config
        provider_config=None,
        policy_path="policies/canary.yaml"
    )

    for event in blocked_events:
        result = executor.execute(
            prompt=event["prompt"],
            mode="enforce"
        )

        # 🚨 Regression detected
        if result["blocked"] is False:
            failures.append({
                "prompt": event["prompt"],
                "active_blocked": True,
                "canary_blocked": False,
                "risk": result.get("risk", 0.0),
            })

    return {
        "safe": len(failures) <= MAX_ALLOWED_REGRESSIONS,
        "failures": failures
    }


def load_recent_events(limit=50):
    """Lightweight loader for recent audit events"""
    import os, json

    files = sorted(
        os.listdir("audit/logs"),
        reverse=True
    )[:limit]

    events = []
    for f in files:
        with open(f"audit/logs/{f}") as fh:
            events.append(json.load(fh))

    return events