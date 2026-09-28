from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models import JobPosting, Skill, User, UserRole
from app.schemas import schemas

router = APIRouter()


def serialize_job(job: JobPosting) -> dict:
    return {
        "id": job.id,
        "employer_id": job.employer_id,
        "title": job.title,
        "role_family": job.role_family,
        "industry": job.industry,
        "district": job.district,
        "state": job.state,
        "employment_type": job.employment_type,
        "salary_band": job.salary_band,
        "experience_min_years": job.experience_min_years,
        "is_active": job.is_active,
        "posted_at": job.posted_at,
        "closing_date": job.closing_date,
        "skill_ids": [skill.id for skill in job.skills],
        "skill_names": [skill.name for skill in job.skills],
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }


@router.post("", response_model=schemas.JobPostingResponse)
def create_job_posting(
    posting_in: schemas.JobPostingCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.EMPLOYER])),
):
    employer = current_user.employer
    if not employer:
        raise HTTPException(status_code=400, detail="Employer profile not created yet")

    skills = []
    if posting_in.skill_ids:
        skills = db.query(Skill).filter(Skill.id.in_(posting_in.skill_ids)).all()
        if len(skills) != len(set(posting_in.skill_ids)):
            raise HTTPException(status_code=400, detail="One or more skills do not exist")

    payload = posting_in.model_dump(exclude={"skill_ids", "posted_at"})
    job = JobPosting(
        employer_id=employer.id,
        posted_at=posting_in.posted_at,
        **payload,
    )
    job.skills = skills
    db.add(job)
    db.commit()
    db.refresh(job)
    return serialize_job(job)


@router.get("/mine", response_model=List[schemas.JobPostingResponse])
def list_my_jobs(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.EMPLOYER])),
):
    employer = current_user.employer
    if not employer:
        return []
    jobs = db.query(JobPosting).filter(JobPosting.employer_id == employer.id).order_by(JobPosting.posted_at.desc()).all()
    return [serialize_job(job) for job in jobs]


@router.get("", response_model=List[schemas.JobPostingResponse])
def list_jobs(
    role_family: str | None = None,
    district: str | None = None,
    state: str | None = None,
    db: Session = Depends(deps.get_db),
):
    query = db.query(JobPosting).filter(JobPosting.is_active.is_(True))
    if role_family:
        query = query.filter(JobPosting.role_family.ilike(f"%{role_family}%"))
    if district:
        query = query.filter(JobPosting.district.ilike(f"%{district}%"))
    if state:
        query = query.filter(JobPosting.state.ilike(f"%{state}%"))
    jobs = query.order_by(JobPosting.posted_at.desc()).limit(100).all()
    return [serialize_job(job) for job in jobs]


@router.delete("/{job_id}")
def deactivate_job(
    job_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker([UserRole.EMPLOYER])),
):
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    if not current_user.employer or job.employer_id != current_user.employer.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this job")
    job.is_active = False
    db.commit()
    return {"status": "deactivated"}
