"""Add Phase 3 demo data to an already-seeded KaushalSetu database.

This script intentionally does not recreate or delete the core Phase 2/3A seed data.
It upgrades a small subset of existing demo enrollments so certificate and outcome
flows can be demonstrated safely.
"""
import os
import sys
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models import (
    User,
    UserRole,
    TrainingEnrollment,
    EnrollmentStatus,
    Assessment,
    AssessmentResult,
    Certificate,
    OutcomeCheckIn,
    OutcomeEmploymentStatus,
)
from app.services.certificate_service import CertificateService


def seed_phase3() -> None:
    db = SessionLocal()
    try:
        provider = db.query(User).filter(User.role == UserRole.TRAINING_PROVIDER).first()
        learner = db.query(User).filter(User.email == "learner1@example.com").first()
        if not provider or not learner or not learner.learner_profile:
            raise RuntimeError("Run the main seed script first so demo users and enrollments exist.")

        enrollment = (
            db.query(TrainingEnrollment)
            .filter(TrainingEnrollment.learner_id == learner.learner_profile.id)
            .order_by(TrainingEnrollment.enrollment_date.asc())
            .first()
        )
        if not enrollment:
            raise RuntimeError("No learner enrollment found for learner1@example.com.")

        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completion_percentage = 100
        enrollment.completion_date = enrollment.completion_date or date.today()

        assessments = (
            db.query(Assessment)
            .filter(Assessment.training_program_id == enrollment.training_program_id)
            .all()
        )
        for assessment in assessments:
            result = (
                db.query(AssessmentResult)
                .filter(
                    AssessmentResult.assessment_id == assessment.id,
                    AssessmentResult.learner_id == enrollment.learner_id,
                )
                .order_by(AssessmentResult.attempt_number.desc())
                .first()
            )
            if not result or not result.passed:
                score = max(assessment.passing_score, assessment.max_score * 0.8)
                if result:
                    result.score = score
                    result.percentage = (score / assessment.max_score) * 100
                    result.passed = True
                else:
                    db.add(
                        AssessmentResult(
                            assessment_id=assessment.id,
                            learner_id=enrollment.learner_id,
                            attempt_number=1,
                            score=score,
                            percentage=(score / assessment.max_score) * 100,
                            passed=True,
                            remarks="Phase 3 demo result",
                        )
                    )
        db.commit()
        db.refresh(enrollment)

        certificate = db.query(Certificate).filter(Certificate.enrollment_id == enrollment.id).first()
        if not certificate:
            skills = []
            if enrollment.learner.skills:
                skills = [item.skill_id for item in enrollment.learner.skills[:3]]
            certificate = CertificateService.issue(
                db,
                enrollment,
                certificate_name=f"{enrollment.training_program.name} Certificate",
                skill_ids=skills,
            )

        existing_checkin = (
            db.query(OutcomeCheckIn)
            .filter(
                OutcomeCheckIn.learner_id == enrollment.learner_id,
                OutcomeCheckIn.milestone_months == 3,
            )
            .first()
        )
        if not existing_checkin:
            db.add(
                OutcomeCheckIn(
                    learner_id=enrollment.learner_id,
                    milestone_months=3,
                    check_in_date=date.today(),
                    employment_status=OutcomeEmploymentStatus.EMPLOYED,
                    employer_name="DemoTech India",
                    role_title="Junior Analyst",
                    industry="IT",
                    district=enrollment.learner.district,
                    state=enrollment.learner.state,
                    income_band="20000-30000",
                    same_employer=True,
                    training_relevance_score=85,
                    using_training_skills=True,
                    skill_gap_notes="Build deeper cloud and practical tooling experience.",
                )
            )
            db.commit()

        print("Phase 3 demo data added successfully.")
        print(f"Certificate number: {certificate.certificate_number}")
        print(f"Verification code: {certificate.verification_code}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_phase3()
