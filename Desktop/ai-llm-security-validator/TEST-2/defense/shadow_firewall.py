# defense/shadow_firewall.py

from defense.firewall import ResponseValidationFirewall
from defense.policy_store import get_canary_policy_path
from defense.policy_engine import PolicyEngine


class ShadowFirewall:
    """
    Canary policy in observe-only mode.
    NEVER blocks traffic.
    """

    def __init__(self):
        self.firewall = ResponseValidationFirewall()

    def evaluate(self, prompt: str, response: str):
        canary_path = get_canary_policy_path()
        if not canary_path:
            return {
                "blocked": False,
                "risk": 0.0
            }

        # Load canary policy explicitly
        self.firewall.policy = PolicyEngine(canary_path)
        self.firewall.policy_mode = "canary"

        req = self.firewall.inspect_request(prompt)
        res = self.firewall.inspect_response(response)

        risk = max(req.get("risk", 0.0), res.get("risk", 0.0))
        blocked = bool(req["violations"] or res["violations"])

        return {
            "blocked": blocked,
            "risk": risk
        }