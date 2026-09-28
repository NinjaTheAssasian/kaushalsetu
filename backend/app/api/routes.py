from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api import deps
from app.api.endpoints import auth, apaar, learners, training, enrollments, skills, assessments, certificates, employment, employers, jobs, admin_analytics

router = APIRouter()

@router.get("/health", tags=["system"])
def health(db: Session = Depends(deps.get_db)) -> dict[str, str]:
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"
        
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "service": "kaushalsetu-api",
        "database": db_status
    }

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(apaar.router, prefix="/apaar", tags=["apaar"])
router.include_router(learners.router, prefix="/learners", tags=["learners"])
router.include_router(training.router, prefix="/training-programs", tags=["training-programs"])
router.include_router(enrollments.router, prefix="/enrollments", tags=["enrollments"])
router.include_router(skills.router, prefix="/skills", tags=["skills"])
router.include_router(assessments.router, prefix="/assessments", tags=["assessments"])
router.include_router(certificates.router, prefix="/certificates", tags=["certificates"])
router.include_router(employment.router, prefix="/employment", tags=["employment"])
router.include_router(employers.router, prefix="/employers", tags=["employers"])

router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(admin_analytics.router, prefix="/admin/analytics", tags=["government-analytics"])
