from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models import User, UserRole, Employer, EmploymentRecord
from app.schemas import schemas

router = APIRouter()
require_employer = deps.RoleChecker([UserRole.EMPLOYER])


@router.get("/me", response_model=schemas.EmployerResponse)
def get_my_employer_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_employer),
):
    employer = db.query(Employer).filter(Employer.user_id == current_user.id).first()
    if not employer:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    return employer


@router.put("/me", response_model=schemas.EmployerResponse)
def upsert_my_employer_profile(
    employer_in: schemas.EmployerBase,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_employer),
):
    employer = db.query(Employer).filter(Employer.user_id == current_user.id).first()
    if not employer:
        employer = Employer(user_id=current_user.id, **employer_in.model_dump())
        db.add(employer)
    else:
        for key, value in employer_in.model_dump().items():
            setattr(employer, key, value)
    db.commit()
    db.refresh(employer)
    return employer


@router.get("/me/employments", response_model=List[schemas.EmploymentRecordResponse])
def get_verified_employments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_employer),
):
    employer = current_user.employer
    if not employer:
        return []
    records = (
        db.query(EmploymentRecord)
        .filter(EmploymentRecord.employer_id == employer.id)
        .order_by(EmploymentRecord.start_date.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "learner_id": r.learner_id,
            "employer_id": r.employer_id,
            "employer_name": employer.organization_name,
            "role_title": r.role_title,
            "reported_employer_name": r.reported_employer_name,
            "industry": r.industry,
            "employment_type": r.employment_type,
            "district": r.district,
            "state": r.state,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "salary_band": r.salary_band,
            "status": r.status,
            "verification_status": r.verification_status,
            "verified_at": r.verified_at,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
        }
        for r in records
    ]
