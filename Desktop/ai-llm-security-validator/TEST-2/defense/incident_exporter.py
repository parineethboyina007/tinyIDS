# defense/incident_exporter.py

import os
import json
from datetime import datetime

from defense.metrics_store import snapshot
from defense.rollback_explanation_store import list_explanations
from defense.rollback_approver import load_latest_approval
from defense.canary_isolation import load_isolation
from defense.rollback_lineage import build_rollback_lineage

INCIDENT_DIR = "audit/incidents"
os.makedirs(INCIDENT_DIR, exist_ok=True)

def export_incident(tenant: str, mode: str) -> dict:
    now = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    metrics = snapshot()
    explanations = list_explanations(tenant, mode)
    latest_explanation = explanations[-1] if explanations else None

    approval = load_latest_approval(tenant, mode)
    isolation = load_isolation(tenant)
    lineage = build_rollback_lineage(tenant, mode)

    incident = {
        "tenant": tenant,
        "mode": mode,
        "exported_at": datetime.utcnow().isoformat(),
        "metrics_snapshot": metrics,
        "rollback_explanation": latest_explanation,
        "rollback_approval": approval,
        "canary_isolation": isolation,
        "lineage": lineage,
        "integrity": lineage.get("integrity") if lineage else None,
    }

    filename = f"incident_{tenant}_{mode}_{now}.json"
    path = os.path.join(INCIDENT_DIR, filename)

    with open(path, "w") as f:
        json.dump(incident, f, indent=2)

    return {
        "status": "exported",
        "incident_file": path,
        "tenant": tenant,
        "mode": mode,
    }