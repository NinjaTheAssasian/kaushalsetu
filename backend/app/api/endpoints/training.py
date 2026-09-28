from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models import User, UserRole, TrainingProvider, TrainingProgram, TrainingEnrollment
from app.schemas import schemas

router = APIRouter()
require_provider = deps.RoleChecker([UserRole.TRAINING_PROVIDER])

@router.post("/programs", response_model=schemas.TrainingProgramResponse)
def create_training_program(
    program_in: schemas.TrainingProgramCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_provider)
):
    provider = db.query(TrainingProvider).filter(TrainingProvider.user_id == current_user.id).first()
    if not provider:
        # Auto-create provider profile if it doesn't exist for demo purposes
        provider = TrainingProvider(
            user_id=current_user.id,
            organization_name="Default Organization",
            registration_number="REG-000",
            district="Default District",
            state="Default State"
        )
        db.add(provider)
        db.commit()
        db.refresh(provider)
        
    program = TrainingProgram(
        provider_id=provider.id,
        **program_in.model_dump()
    )
    db.add(program)
    db.commit()
    db.refresh(program)
    return program

@router.get("/programs", response_model=List[schemas.TrainingProgramResponse])
def get_training_programs(
    db: Session = Depends(deps.get_db)
):
    # Publicly accessible for phase 2
    programs = db.query(TrainingProgram).filter(TrainingProgram.is_active == True).all()
    return programs


@router.get("/{program_id}/enrollments", response_model=List[schemas.TrainingEnrollmentResponse])
def get_program_enrollments(
    program_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_provider),
):
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
    provider = current_user.training_provider
    if not provider or program.provider_id != provider.id:
        raise HTTPException(status_code=403, detail="Not authorized to view enrollments for this program")
    return (
        db.query(TrainingEnrollment)
        .filter(TrainingEnrollment.training_program_id == program.id)
        .order_by(TrainingEnrollment.enrollment_date.desc())
        .all()
    )

@router.post("/{program_id}/assessments", response_model=schemas.AssessmentResponse)
def create_assessment(
    program_id: str,
    assessment_in: schemas.AssessmentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_provider)
):
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
        
    provider = current_user.training_provider
    if not provider or program.provider_id != provider.id:
        raise HTTPException(status_code=403, detail="Not authorized to create assessment for this program")
        
    from app.models import Assessment
    assessment = Assessment(
        training_program_id=program.id,
        **assessment_in.model_dump()
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment

@router.get("/{program_id}/assessments", response_model=List[schemas.AssessmentResponse])
def get_assessments(
    program_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    program = db.query(TrainingProgram).filter(TrainingProgram.id == program_id).first()
    if not program:
        raise HTTPException(status_code=404, detail="Training program not found")
        
    # Anyone authenticated can see assessments for a program (or limit to enrolled trainees + admin + provider)
    # The prompt doesn't explicitly limit reading assessments entirely, but let's just return them.
    from app.models import Assessment
    assessments = db.query(Assessment).filter(Assessment.training_program_id == program.id).all()
    return assessments
