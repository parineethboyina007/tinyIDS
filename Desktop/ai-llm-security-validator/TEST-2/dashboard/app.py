from fastapi import FastAPI
from defense.policy_metrics_engine import get_security_metrics
from defense.policy_timeline_engine import replay_policy_timeline
from defense.policy_explainability_engine import explain_policy_decision
from defense.trust_safety_report_engine import generate_trust_safety_report

app = FastAPI(title="Governance Dashboard", docs_url=None, redoc_url=None)

@app.get("/dashboard/metrics/{tenant}")
def metrics(tenant: str):
    return get_security_metrics(tenant)

@app.get("/dashboard/timeline/{tenant}/{rule_id}")
def timeline(tenant: str, rule_id: str):
    return replay_policy_timeline(tenant, rule_id)

@app.get("/dashboard/trust-safety/{tenant}")
def trust_safety(tenant: str):
    return generate_trust_safety_report(tenant)