from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models import (
    User,
    UserRole,
    Employer,
    EmploymentRecord,
    EmploymentVerificationStatus,
    EmployerSkillFeedback,
    LearnerProfile,
    Skill,
    LearnerSkill,
)
from app.schemas import schemas
from app.services.employment_service import EmploymentService

router = APIRouter()


def _serialize_record(record: EmploymentRecord, include_code: str | None = None):
    payload = {
        "id": record.id,
        "learner_id": record.learner_id,
        "employer_id": record.employer_id,
        "employer_name": record.employer.organization_name if record.employer else None,
        "role_title": record.role_title,
        "reported_employer_name": record.reported_employer_name,
        "industry": record.industry,
        "employment_type": record.employment_type,
        "district": record.district,
        "state": record.state,
        "start_date": record.start_date,
        "end_date": record.end_date,
        "salary_band": record.salary_band,
        "status": record.status,
        "verification_status": record.verification_status,
        "verified_at": record.verified_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }
    if include_code is not None:
        payload["verification_code"] = include_code
    return payload


@router.post("/verify", response_model=schemas.EmploymentVerificationResponse)
def verify_employment(
    verification_in: schemas.EmploymentVerificationRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.EMPLOYER])),
):
    employer = current_user.employer
    if not employer:
        raise HTTPException(status_code=400, detail="Employer profile not created yet")
    try:
        record = EmploymentService.verify(db, employer, verification_in.verification_code.strip())
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return schemas.EmploymentVerificationResponse(
        id=record.id,
        status=record.verification_status,
        employer_name=record.employer.organization_name if record.employer else None,
        role_title=record.role_title,
        start_date=record.start_date,
        message="Employment verified successfully.",
    )


@router.get("/{employment_id}", response_model=schemas.EmploymentRecordResponse)
def get_employment_record(
    employment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    record = db.query(EmploymentRecord).filter(EmploymentRecord.id == employment_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Employment record not found")

    allowed = False
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        allowed = True
    elif current_user.role == UserRole.TRAINEE:
        allowed = bool(current_user.learner_profile and record.learner_id == current_user.learner_profile.id)
    elif current_user.role == UserRole.EMPLOYER:
        allowed = bool(current_user.employer and record.employer_id == current_user.employer.id)
    if not allowed:
        raise HTTPException(status_code=403, detail="Not authorized to view this employment record")

    return _serialize_record(record)


@router.post("/{employment_id}/feedback", response_model=schemas.EmployerSkillFeedbackResponse)
def submit_skill_feedback(
    employment_id: uuid.UUID,
    feedback_in: schemas.EmployerSkillFeedbackCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.EMPLOYER])),
):
    employer = current_user.employer
    if not employer:
        raise HTTPException(status_code=400, detail="Employer profile not created yet")

    record = db.query(EmploymentRecord).filter(EmploymentRecord.id == employment_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Employment record not found")
    if record.employer_id != employer.id or record.verification_status != EmploymentVerificationStatus.EMPLOYER_VERIFIED:
        raise HTTPException(status_code=403, detail="Employment must be verified by this employer first")

    try:
        feedback = EmploymentService.upsert_skill_feedback(
            db,
            record,
            employer,
            feedback_in.skill_id,
            feedback_in.rating,
            feedback_in.comments,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    feedback.skill = db.query(Skill).filter(Skill.id == feedback.skill_id).first()
    return {
        "id": feedback.id,
        "employment_record_id": feedback.employment_record_id,
        "employer_id": feedback.employer_id,
        "skill_id": feedback.skill_id,
        "skill_name": feedback.skill.name if feedback.skill else None,
        "rating": feedback.rating,
        "comments": feedback.comments,
        "created_at": feedback.created_at,
        "updated_at": feedback.updated_at,
    }


@router.get("/{employment_id}/feedback", response_model=List[schemas.EmployerSkillFeedbackResponse])
def get_skill_feedback(
    employment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    record = db.query(EmploymentRecord).filter(EmploymentRecord.id == employment_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Employment record not found")

    allowed = False
    if current_user.role == UserRole.GOVERNMENT_ADMIN:
        allowed = True
    elif current_user.role == UserRole.TRAINEE:
        allowed = bool(current_user.learner_profile and record.learner_id == current_user.learner_profile.id)
    elif current_user.role == UserRole.EMPLOYER:
        allowed = bool(current_user.employer and record.employer_id == current_user.employer.id)
    if not allowed:
        raise HTTPException(status_code=403, detail="Not authorized to view skill feedback")

    feedback_rows = (
        db.query(EmployerSkillFeedback)
        .filter(EmployerSkillFeedback.employment_record_id == record.id)
        .all()
    )
    output = []
    for feedback in feedback_rows:
        skill = db.query(Skill).filter(Skill.id == feedback.skill_id).first()
        output.append({
            "id": feedback.id,
            "employment_record_id": feedback.employment_record_id,
            "employer_id": feedback.employer_id,
            "skill_id": feedback.skill_id,
            "skill_name": skill.name if skill else None,
            "rating": feedback.rating,
            "comments": feedback.comments,
            "created_at": feedback.created_at,
            "updated_at": feedback.updated_at,
        })
    return output
