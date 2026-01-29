from fastapi import APIRouter
from defense.attestation_engine import generate_attestation_pack

router = APIRouter(prefix="/v1/security/attestation")

@router.post("/{tenant}")
def generate_attestation(tenant: str):
    return generate_attestation_pack(tenant)