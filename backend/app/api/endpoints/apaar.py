from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models import User, ApaarIdentity, VerificationStatus
from app.schemas import schemas
from app.services.apaar_service import ApaarVerificationService

router = APIRouter()

@router.post("/verify", response_model=schemas.ApaarIdentityResponse)
def verify_apaar(
    request: schemas.ApaarVerifyRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Mock APAAR verification endpoint. DEMO ONLY.
    """
    try:
        result = ApaarVerificationService.verify_apaar(request.apaar_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Check if identity already exists
    identity = db.query(ApaarIdentity).filter(ApaarIdentity.user_id == current_user.id).first()
    
    if identity:
        identity.masked_apaar_id = result["masked_apaar_id"]
        identity.apaar_hash = result["apaar_hash"]
        identity.verification_status = VerificationStatus.VERIFIED
    else:
        identity = ApaarIdentity(
            user_id=current_user.id,
            masked_apaar_id=result["masked_apaar_id"],
            apaar_hash=result["apaar_hash"],
            verification_status=VerificationStatus.VERIFIED
        )
        db.add(identity)
        
    try:
        db.commit()
        db.refresh(identity)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="APAAR ID already associated with another user")
        
    return identity

@router.get("/status", response_model=schemas.ApaarStatusResponse)
def get_apaar_status(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    identity = db.query(ApaarIdentity).filter(ApaarIdentity.user_id == current_user.id).first()
    if not identity:
        return schemas.ApaarStatusResponse(
            masked_apaar_id="",
            verification_status=VerificationStatus.UNVERIFIED
        )
    return schemas.ApaarStatusResponse(
        masked_apaar_id=identity.masked_apaar_id,
        verification_status=identity.verification_status
    )
