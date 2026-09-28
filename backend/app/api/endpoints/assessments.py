from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api import deps
from app.models import User, UserRole, TrainingProgram, Assessment, AssessmentResult, LearnerProfile, TrainingEnrollment
from app.schemas import schemas

router = APIRouter()
require_provider = deps.RoleChecker([UserRole.TRAINING_PROVIDER])

# These will be registered under /training-programs in routes.py, but we can also handle them here if needed.
# Actually, the simplest way is to put /training-programs/... in training.py and /assessments/... in assessments.py

@router.post("/{assessment_id}/results", response_model=schemas.AssessmentResultResponse)
def record_assessment_result(
    assessment_id: str,
    result_in: schemas.AssessmentResultCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(require_provider)
):
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
        
    program = db.query(TrainingProgram).filter(TrainingProgram.id == assessment.training_program_id).first()
    provider = current_user.training_provider
    if not provider or program.provider_id != provider.id:
        raise HTTPException(status_code=403, detail="Not authorized to record results for this assessment")
        
    if result_in.score < 0 or result_in.score > assessment.max_score:
        raise HTTPException(status_code=400, detail="Score must be between 0 and max_score")
        
    percentage = (result_in.score / assessment.max_score) * 100
    passed = percentage >= assessment.passing_score
    
    result = AssessmentResult(
        assessment_id=assessment.id,
        learner_id=result_in.learner_id,
        score=result_in.score,
        percentage=percentage,
        passed=passed,
        remarks=result_in.remarks,
        attempt_number=result_in.attempt_number
    )
    db.add(result)
    try:
        db.commit()
        db.refresh(result)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Duplicate result for this attempt")
        
    return result
