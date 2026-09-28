import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.api import deps
from app.models import (
    User,
    UserRole,
    LearnerProfile,
    LearnerSkill,
    Skill,
    CareerEvent,
    AssessmentResult,
    Certificate,
    OutcomeCheckIn,
    OutcomeVerificationStatus,
    EmploymentRecord, EmploymentRecordStatus, EmploymentVerificationStatus,
)
from app.schemas import schemas
from app.services.certificate_service import CertificateService
from app.services.employment_service import EmploymentService

router = APIRouter()
require_trainee = deps.RoleChecker([UserRole.TRAINEE])


@router.get("/me", response_model=schemas.LearnerProfileResponse)
def get_my_profile(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/me", response_model=schemas.LearnerProfileResponse)
def update_my_profile(
    profile_in: schemas.LearnerProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        profile = LearnerProfile(user_id=current_user.id, **profile_in.model_dump())
        db.add(profile)
    else:
        for var, value in profile_in.model_dump().items():
            setattr(profile, var, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/me/skills", response_model=schemas.LearnerSkillResponse)
def add_my_skill(
    skill_in: schemas.LearnerSkillCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not created yet")

    skill = db.query(Skill).filter(Skill.id == skill_in.skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    learner_skill = LearnerSkill(
        learner_id=profile.id,
        skill_id=skill.id,
        proficiency_score=skill_in.proficiency_score,
        proficiency_source=skill_in.proficiency_source,
    )
    db.add(learner_skill)
    try:
        db.commit()
        db.refresh(learner_skill)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Skill already added")
    return learner_skill


@router.get("/me/career-events", response_model=list[schemas.CareerEventResponse])
def get_my_career_events(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        return []
    return (
        db.query(CareerEvent)
        .filter(CareerEvent.learner_id == profile.id)
        .order_by(desc(CareerEvent.event_date), desc(CareerEvent.created_at))
        .all()
    )


@router.post("/me/career-events", response_model=schemas.CareerEventResponse)
def add_my_career_event(
    event_in: schemas.CareerEventCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not created yet")

    event = CareerEvent(
        learner_id=profile.id,
        event_type=event_in.event_type,
        title=event_in.title,
        description=event_in.description,
        event_date=event_in.event_date,
        metadata_=event_in.metadata_,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("/me/assessments", response_model=list[schemas.AssessmentResultResponse])
def get_my_assessments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        return []
    return (
        db.query(AssessmentResult)
        .filter(AssessmentResult.learner_id == profile.id)
        .order_by(desc(AssessmentResult.assessed_at))
        .all()
    )




# Phase 4: employment tracking
@router.post("/me/employment", response_model=schemas.EmploymentRecordCreateResponse)
def create_my_employment(
    employment_in: schemas.EmploymentRecordCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not created yet")

    if employment_in.start_date > __import__("datetime").date.today():
        raise HTTPException(status_code=400, detail="start_date cannot be in the future")

    try:
        record, verification_code = EmploymentService.create_self_reported(
            db, profile, employment_in.model_dump()
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
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
        "verification_code": verification_code,
    }


@router.get("/me/employment", response_model=list[schemas.EmploymentRecordResponse])
def get_my_employment(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        return []
    records = (
        db.query(EmploymentRecord)
        .filter(EmploymentRecord.learner_id == profile.id)
        .order_by(EmploymentRecord.start_date.desc(), EmploymentRecord.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "learner_id": r.learner_id,
            "employer_id": r.employer_id,
            "employer_name": r.employer.organization_name if r.employer else None,
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


@router.put("/me/employment/{employment_id}", response_model=schemas.EmploymentRecordResponse)
def update_my_employment(
    employment_id: uuid.UUID,
    employment_in: schemas.EmploymentRecordUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    record = db.query(EmploymentRecord).filter(EmploymentRecord.id == employment_id).first()
    if not profile or not record or record.learner_id != profile.id:
        raise HTTPException(status_code=404, detail="Employment record not found")

    # Employer-verified records remain immutable except for ending employment.
    values = employment_in.model_dump(exclude_none=True)
    disallowed = set(values) & {"role_title", "industry", "employment_type", "salary_band", "district", "state"}
    if disallowed and record.verification_status == EmploymentVerificationStatus.EMPLOYER_VERIFIED:
        raise HTTPException(status_code=409, detail="Employer-verified employment details cannot be edited by the learner")

    if "end_date" in values and values["end_date"] is not None and values["end_date"] < record.start_date:
        raise HTTPException(status_code=400, detail="end_date cannot be before start_date")
    if values.get("status") == EmploymentRecordStatus.ENDED and "end_date" not in values:
        values["end_date"] = __import__("datetime").date.today()

    for key, value in values.items():
        setattr(record, key, value)

    if record.status == EmploymentRecordStatus.ENDED:
        record.verification_status = EmploymentVerificationStatus.REVOKED if record.verification_status == EmploymentVerificationStatus.EMPLOYER_VERIFIED else record.verification_status
        profile.current_employment_status = profile.current_employment_status.SEEKING_EMPLOYMENT
    db.commit()
    db.refresh(record)
    return {
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


@router.post("/me/employment/{employment_id}/end", response_model=schemas.EmploymentRecordResponse)
def end_my_employment(
    employment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    record = db.query(EmploymentRecord).filter(EmploymentRecord.id == employment_id).first()
    if not profile or not record or record.learner_id != profile.id:
        raise HTTPException(status_code=404, detail="Employment record not found")
    if record.status == EmploymentRecordStatus.ENDED:
        raise HTTPException(status_code=400, detail="Employment is already ended")
    EmploymentService.end_employment(db, record)
    db.refresh(record)
    return {
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


@router.post("/me/employment/{employment_id}/verification-code", response_model=schemas.EmploymentRecordCreateResponse)
def rotate_employment_verification_code(
    employment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    record = db.query(EmploymentRecord).filter(EmploymentRecord.id == employment_id).first()
    if not profile or not record or record.learner_id != profile.id:
        raise HTTPException(status_code=404, detail="Employment record not found")
    try:
        code = EmploymentService.rotate_verification_code(db, record)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
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
        "verification_code": code,
    }


@router.post("/me/outcomes", response_model=schemas.OutcomeCheckInResponse)
def submit_outcome_checkin(
    checkin_in: schemas.OutcomeCheckInCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not created yet")

    if checkin_in.milestone_months not in {3, 6, 12}:
        raise HTTPException(status_code=400, detail="milestone_months must be one of 3, 6, or 12")
    if checkin_in.training_relevance_score is not None and not 0 <= checkin_in.training_relevance_score <= 100:
        raise HTTPException(status_code=400, detail="training_relevance_score must be between 0 and 100")

    existing = (
        db.query(OutcomeCheckIn)
        .filter(
            OutcomeCheckIn.learner_id == profile.id,
            OutcomeCheckIn.milestone_months == checkin_in.milestone_months,
        )
        .first()
    )
    values = checkin_in.model_dump(exclude_none=True)
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
        existing.verification_status = OutcomeVerificationStatus.SELF_REPORTED
        db.commit()
        db.refresh(existing)
        return existing

    checkin = OutcomeCheckIn(
        learner_id=profile.id,
        verification_status=OutcomeVerificationStatus.SELF_REPORTED,
        **values,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return checkin


@router.get("/me/outcomes", response_model=list[schemas.OutcomeCheckInResponse])
def get_my_outcomes(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        return []
    return (
        db.query(OutcomeCheckIn)
        .filter(OutcomeCheckIn.learner_id == profile.id)
        .order_by(OutcomeCheckIn.milestone_months.asc())
        .all()
    )


@router.get("/me/timeline", response_model=list[schemas.TimelineItem])
def get_my_timeline(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        return []

    items: list[schemas.TimelineItem] = []

    career_events = db.query(CareerEvent).filter(CareerEvent.learner_id == profile.id).all()
    for event in career_events:
        items.append(
            schemas.TimelineItem(
                event_type=event.event_type.value,
                event_date=event.event_date,
                title=event.title,
                description=event.description,
                status=None,
                metadata=event.metadata_,
            )
        )

    from app.models import TrainingEnrollment
    enrollments = db.query(TrainingEnrollment).filter(TrainingEnrollment.learner_id == profile.id).all()
    for enrollment in enrollments:
        program_name = enrollment.training_program.name if enrollment.training_program else "Training Program"
        items.append(
            schemas.TimelineItem(
                event_type="TRAINING_ENROLLMENT",
                event_date=enrollment.enrollment_date,
                title=f"Enrolled in {program_name}",
                description="Training enrollment",
                status=enrollment.status.value,
                metadata={
                    "enrollment_id": str(enrollment.id),
                    "completion_percentage": enrollment.completion_percentage,
                    "attendance_percentage": enrollment.attendance_percentage,
                },
            )
        )
        if enrollment.completion_date:
            items.append(
                schemas.TimelineItem(
                    event_type="TRAINING_COMPLETED",
                    event_date=enrollment.completion_date,
                    title=f"Completed {program_name}",
                    description="Training completion",
                    status=enrollment.status.value,
                    metadata={"enrollment_id": str(enrollment.id)},
                )
            )

    results = db.query(AssessmentResult).filter(AssessmentResult.learner_id == profile.id).all()
    for result in results:
        items.append(
            schemas.TimelineItem(
                event_type="ASSESSMENT_RESULT",
                event_date=result.assessed_at.date(),
                title="Assessment result recorded",
                description=f"Score {result.score} ({result.percentage:.1f}%)",
                status="PASSED" if result.passed else "FAILED",
                metadata={
                    "assessment_id": str(result.assessment_id),
                    "attempt_number": result.attempt_number,
                },
            )
        )

    certificates = db.query(Certificate).filter(Certificate.learner_id == profile.id).all()
    for certificate in certificates:
        items.append(
            schemas.TimelineItem(
                event_type="CERTIFICATION",
                event_date=certificate.issue_date,
                title=certificate.certificate_name,
                description="Certificate issued",
                status=certificate.status.value,
                metadata={
                    "certificate_id": str(certificate.id),
                    "certificate_number": certificate.certificate_number,
                    "skills": [skill.name for skill in certificate.skills],
                },
            )
        )

    checkins = db.query(OutcomeCheckIn).filter(OutcomeCheckIn.learner_id == profile.id).all()
    for checkin in checkins:
        items.append(
            schemas.TimelineItem(
                event_type="OUTCOME_CHECK_IN",
                event_date=checkin.check_in_date,
                title=f"{checkin.milestone_months}-month career check-in",
                description="Longitudinal outcome update",
                status=checkin.employment_status.value,
                metadata={
                    "role_title": checkin.role_title,
                    "income_band": checkin.income_band,
                    "training_relevance_score": checkin.training_relevance_score,
                    "verification_status": checkin.verification_status.value,
                },
            )
        )

    return sorted(items, key=lambda item: item.event_date, reverse=True)
