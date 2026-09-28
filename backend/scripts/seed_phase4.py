"""Seed a small Phase 4 employer-verification demo on top of Phase 3 data."""
import os
import sys
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models import (
    User,
    UserRole,
    Employer,
    EmploymentRecord,
    EmploymentVerificationStatus,
    Skill,
    LearnerSkill,
    ProficiencySource,
)
from app.services.employment_service import EmploymentService


def seed_phase4() -> None:
    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.email == "learner1@example.com").first()
        employer = (
            db.query(Employer)
            .join(User, Employer.user_id == User.id)
            .filter(User.role == UserRole.EMPLOYER)
            .order_by(User.email.asc())
            .first()
        )
        if not learner or not learner.learner_profile or not employer:
            raise RuntimeError("Run seed_db.py first so Phase 2/3 learner and employer demo data exist.")

        employer_user = db.query(User).filter(User.id == employer.user_id).first()
        if not employer_user:
            raise RuntimeError("Employer user for the employer profile was not found.")

        record = (
            db.query(EmploymentRecord)
            .filter(EmploymentRecord.learner_id == learner.learner_profile.id)
            .order_by(EmploymentRecord.created_at.asc())
            .first()
        )

        verification_code = None
        if not record:
            record, verification_code = EmploymentService.create_self_reported(
                db,
                learner.learner_profile,
                {
                    "role_title": "Junior Security Analyst",
                    "reported_employer_name": employer.organization_name,
                    "industry": employer.industry,
                    "employment_type": "FULL_TIME",
                    "district": employer.district,
                    "state": employer.state,
                    "start_date": date.today() - timedelta(days=30),
                    "salary_band": "25000-35000",
                },
            )

        if record.verification_status != EmploymentVerificationStatus.EMPLOYER_VERIFIED:
            if verification_code is None:
                print("An employment record already exists but its verification code was not retained by this seed script.")
                print("Create a new demo employment record through the learner UI to generate a fresh code.")
            else:
                record = EmploymentService.verify(db, employer, verification_code)
                print(f"Employer verification complete for {record.role_title}.")

        skill = db.query(Skill).filter(Skill.name == "Python").first() or db.query(Skill).first()
        if skill and record.verification_status == EmploymentVerificationStatus.EMPLOYER_VERIFIED:
            from app.models import EmployerSkillFeedback
            feedback = (
                db.query(EmployerSkillFeedback)
                .filter(
                    EmployerSkillFeedback.employment_record_id == record.id,
                    EmployerSkillFeedback.skill_id == skill.id,
                )
                .first()
            )
            if not feedback:
                EmploymentService.upsert_skill_feedback(
                    db,
                    record,
                    employer,
                    skill.id,
                    86,
                    "Strong practical usage; improve production troubleshooting depth.",
                )

        print("Phase 4 demo data ready.")
        print(f"Employment record: {record.id}")
        print(f"Verification status: {record.verification_status.value}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_phase4()
