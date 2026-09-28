from datetime import date
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models import (
    User,
    UserRole,
    LearnerProfile,
    TrainingEnrollment,
    TrainingProgram,
    CareerEvent,
    CareerEventType,
    EnrollmentStatus,
    Certificate,
)
from app.schemas import schemas
from app.services.certificate_service import CertificateEligibilityService, CertificateService

router = APIRouter()
require_trainee = deps.RoleChecker([UserRole.TRAINEE])
require_provider = deps.RoleChecker([UserRole.TRAINING_PROVIDER])


@router.post("/", response_model=schemas.TrainingEnrollmentResponse)
def enroll_in_program(
    enrollment_in: schemas.TrainingEnrollmentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=400, detail="Profile not created yet")

    program = db.query(TrainingProgram).filter(TrainingProgram.id == enrollment_in.training_program_id).first()
    if not program or not program.is_active:
        raise HTTPException(status_code=404, detail="Training program not found or inactive")

    enrollment = TrainingEnrollment(
        learner_id=profile.id,
        training_program_id=program.id,
        status=EnrollmentStatus.ENROLLED,
        completion_percentage=0,
        attendance_percentage=0,
    )
    db.add(enrollment)
    try:
        db.flush()
        db.add(
            CareerEvent(
                learner_id=profile.id,
                event_type=CareerEventType.ENROLLMENT,
                title=f"Enrolled in {program.name}",
                description="Learner enrolled in a training program.",
                event_date=enrollment.enrollment_date or date.today(),
                metadata_={"training_program_id": str(program.id), "enrollment_id": str(enrollment.id)},
            )
        )
        db.commit()
        db.refresh(enrollment)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Already enrolled in this program")

    return enrollment


@router.get("/me", response_model=List[schemas.TrainingEnrollmentResponse])
def get_my_enrollments(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_trainee),
):
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        return []

    enrollments = (
        db.query(TrainingEnrollment)
        .filter(TrainingEnrollment.learner_id == profile.id)
        .order_by(TrainingEnrollment.enrollment_date.desc())
        .all()
    )
    return enrollments


@router.put("/{enrollment_id}/progress", response_model=schemas.TrainingEnrollmentResponse)
def update_enrollment_progress(
    enrollment_id: uuid.UUID,
    progress_in: schemas.TrainingEnrollmentProgressUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_provider),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    program = db.query(TrainingProgram).filter(TrainingProgram.id == enrollment.training_program_id).first()
    if not program or not current_user.training_provider or program.provider_id != current_user.training_provider.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this enrollment")

    if progress_in.completion_percentage is not None and not 0 <= progress_in.completion_percentage <= 100:
        raise HTTPException(status_code=400, detail="completion_percentage must be between 0 and 100")

    old_status = enrollment.status
    if progress_in.status is not None:
        enrollment.status = progress_in.status
    if progress_in.completion_percentage is not None:
        enrollment.completion_percentage = progress_in.completion_percentage
    if progress_in.completion_date is not None:
        enrollment.completion_date = progress_in.completion_date

    if enrollment.status == EnrollmentStatus.COMPLETED:
        enrollment.completion_percentage = max(enrollment.completion_percentage or 0, 100)
        enrollment.completion_date = enrollment.completion_date or date.today()
        if old_status != EnrollmentStatus.COMPLETED:
            db.add(
                CareerEvent(
                    learner_id=enrollment.learner_id,
                    event_type=CareerEventType.TRAINING_COMPLETED,
                    title=f"Completed {program.name}",
                    description="Training program completed.",
                    event_date=enrollment.completion_date,
                    metadata_={"training_program_id": str(program.id), "enrollment_id": str(enrollment.id)},
                )
            )

    db.commit()
    db.refresh(enrollment)
    return enrollment


@router.post("/{enrollment_id}/certificate", response_model=schemas.CertificateResponse)
def issue_certificate_for_enrollment(
    enrollment_id: uuid.UUID,
    issue_in: schemas.CertificateIssueRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_provider),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    program = db.query(TrainingProgram).filter(TrainingProgram.id == enrollment.training_program_id).first()
    if not program or not current_user.training_provider or program.provider_id != current_user.training_provider.id:
        raise HTTPException(status_code=403, detail="Not authorized to issue a certificate for this enrollment")

    certificate_name = issue_in.certificate_name or f"{program.name} Certificate"
    try:
        certificate = CertificateService.issue(
            db,
            enrollment,
            certificate_name=certificate_name,
            skill_ids=issue_in.skill_ids,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CertificateService.serialize(certificate)


@router.get("/{enrollment_id}/certificate-eligibility", response_model=schemas.CertificateEligibilityResponse)
def enrollment_certificate_eligibility(
    enrollment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if current_user.role == UserRole.TRAINEE:
        if not current_user.learner_profile or enrollment.learner_id != current_user.learner_profile.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.TRAINING_PROVIDER:
        program = db.query(TrainingProgram).filter(TrainingProgram.id == enrollment.training_program_id).first()
        if not current_user.training_provider or not program or program.provider_id != current_user.training_provider.id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role != UserRole.GOVERNMENT_ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    eligible, reasons = CertificateEligibilityService.check(db, enrollment)
    return schemas.CertificateEligibilityResponse(eligible=eligible, reasons=reasons)


@router.post("/{enrollment_id}/attendance", response_model=schemas.AttendanceRecordResponse)
def record_attendance(
    enrollment_id: uuid.UUID,
    attendance_in: schemas.AttendanceRecordCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_provider),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    program = db.query(TrainingProgram).filter(TrainingProgram.id == enrollment.training_program_id).first()
    if not program or not current_user.training_provider or program.provider_id != current_user.training_provider.id:
        raise HTTPException(status_code=403, detail="Not authorized to record attendance")

    from app.models import AttendanceRecord

    record = AttendanceRecord(enrollment_id=enrollment.id, **attendance_in.model_dump())
    db.add(record)
    try:
        db.flush()
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate attendance record for this date")

    total_records = db.query(AttendanceRecord).filter(AttendanceRecord.enrollment_id == enrollment.id).count()
    present_records = (
        db.query(AttendanceRecord)
        .filter(
            AttendanceRecord.enrollment_id == enrollment.id,
            AttendanceRecord.status == "PRESENT",
        )
        .count()
    )
    enrollment.attendance_percentage = (present_records / total_records) * 100 if total_records else 0
    db.commit()
    db.refresh(record)
    return record


@router.get("/{enrollment_id}/attendance", response_model=List[schemas.AttendanceRecordResponse])
def get_attendance(
    enrollment_id: uuid.UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    enrollment = db.query(TrainingEnrollment).filter(TrainingEnrollment.id == enrollment_id).first()
    if not enrollment:
        raise HTTPException(status_code=404, detail="Enrollment not found")

    if current_user.role == UserRole.TRAINEE:
        if current_user.learner_profile and enrollment.learner_id != current_user.learner_profile.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this attendance")
    elif current_user.role == UserRole.TRAINING_PROVIDER:
        program = db.query(TrainingProgram).filter(TrainingProgram.id == enrollment.training_program_id).first()
        if not current_user.training_provider or not program or program.provider_id != current_user.training_provider.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this attendance")
    elif current_user.role not in {UserRole.GOVERNMENT_ADMIN}:
        raise HTTPException(status_code=403, detail="Not authorized")

    from app.models import AttendanceRecord
    return (
        db.query(AttendanceRecord)
        .filter(AttendanceRecord.enrollment_id == enrollment.id)
        .order_by(AttendanceRecord.attendance_date.desc())
        .all()
    )
