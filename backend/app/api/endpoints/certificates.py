from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.api import deps
from app.models import (
    Certificate,
    CertificateStatus,
    Skill,
    User,
    UserRole,
)
from app.schemas import schemas
from app.services.certificate_service import CertificateService

router = APIRouter()


@router.get("/me", response_model=List[schemas.CertificateResponse])
def get_my_certificates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.TRAINEE])),
):
    if not current_user.learner_profile:
        return []
    certificates = (
        db.query(Certificate)
        .filter(Certificate.learner_id == current_user.learner_profile.id)
        .order_by(Certificate.issue_date.desc())
        .all()
    )
    return [CertificateService.serialize(certificate) for certificate in certificates]


@router.get("/verify/{verification_code}", response_model=schemas.CertificateVerificationResponse)
def verify_certificate(
    verification_code: str,
    db: Session = Depends(deps.get_db),
):
    certificate = (
        db.query(Certificate)
        .filter(Certificate.verification_code == verification_code)
        .first()
    )
    if not certificate:
        return schemas.CertificateVerificationResponse(valid=False)

    return schemas.CertificateVerificationResponse(
        valid=certificate.status == CertificateStatus.ISSUED,
        certificate_number=certificate.certificate_number,
        certificate_name=certificate.certificate_name,
        issued_on=certificate.issue_date,
        status=certificate.status,
        program_name=certificate.training_program.name,
        skills=[skill.name for skill in certificate.skills],
    )


@router.post("/{certificate_id}/revoke", response_model=schemas.CertificateResponse)
def revoke_certificate(
    certificate_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    allowed = current_user.role == UserRole.GOVERNMENT_ADMIN or (
        current_user.role == UserRole.TRAINING_PROVIDER
        and current_user.training_provider is not None
        and certificate.training_program.provider_id == current_user.training_provider.id
    )
    if not allowed:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this certificate")

    if certificate.status == CertificateStatus.REVOKED:
        return CertificateService.serialize(certificate)

    certificate.status = CertificateStatus.REVOKED
    db.commit()
    db.refresh(certificate)
    return CertificateService.serialize(certificate)


@router.get("/{certificate_id}", response_model=schemas.CertificateResponse)
def get_certificate(
    certificate_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")

    allowed = False
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        allowed = True
    elif current_user.role == UserRole.TRAINEE:
        allowed = bool(current_user.learner_profile and certificate.learner_id == current_user.learner_profile.id)
    elif current_user.role == UserRole.TRAINING_PROVIDER:
        allowed = bool(current_user.training_provider and certificate.training_program.provider_id == current_user.training_provider.id)
    elif current_user.role == UserRole.EMPLOYER:
        # Employers should normally use the public verification endpoint; don't expose
        # certificate details through authenticated employer endpoints.
        allowed = False

    if not allowed:
        raise HTTPException(status_code=403, detail="Not authorized to view this certificate")

    return CertificateService.serialize(certificate)


@router.get("/eligibility/{enrollment_id}", response_model=schemas.CertificateEligibilityResponse)
def certificate_eligibility(
    enrollment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    from app.models import TrainingEnrollment
    from app.services.certificate_service import CertificateEligibilityService

    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if current_user.role == UserRole.TRAINEE:
        if not current_user.learner_profile or enrollment.learner_id != current_user.learner_profile.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.TRAINING_PROVIDER:
        if not current_user.training_provider or enrollment.training_program.provider_id != current_user.training_provider.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role != UserRole.GOVERNMENT_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    eligible, reasons = CertificateEligibilityService.check(db, enrollment)
    return schemas.CertificateEligibilityResponse(eligible=eligible, reasons=reasons)
