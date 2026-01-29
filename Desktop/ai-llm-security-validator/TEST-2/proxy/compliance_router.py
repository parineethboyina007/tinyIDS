# proxy/compliance_router.py

from fastapi import APIRouter, Query, HTTPException

from defense.compliance_export_engine import export_compliance_evidence

router = APIRouter(prefix="/v1/compliance", tags=["compliance"])


@router.get("/export")
def export_compliance(
    tenant: str = Query("default", description="Tenant identifier"),
):
    """
    STEP-78 — Secure Compliance Export Endpoint

    Read-only.
    No mutation.
    Safe for auditors.
    """

    try:
        result = export_compliance_evidence(tenant)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Compliance export failed: {str(e)}"
        )