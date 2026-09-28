import secrets
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssessmentResult,
    Certificate,
    CertificateStatus,
    CareerEvent,
    CareerEventType,
    EnrollmentStatus,
    LearnerSkill,
    ProficiencySource,
    Skill,
    TrainingEnrollment,
)


class CertificateEligibilityService:
    @staticmethod
    def check(db: Session, enrollment: TrainingEnrollment) -> tuple[bool, list[str]]:
        reasons: list[str] = []

        if enrollment.status != EnrollmentStatus.COMPLETED and (enrollment.completion_percentage or 0) < 100:
            reasons.append("Training enrollment is not completed")

        assessments = (
            db.query(Assessment)
            .filter(Assessment.training_program_id == enrollment.training_program_id)
            .all()
        )

        for assessment in assessments:
            passed = (
                db.query(AssessmentResult)
                .filter(
                    AssessmentResult.assessment_id == assessment.id,
                    AssessmentResult.learner_id == enrollment.learner_id,
                    AssessmentResult.passed.is_(True),
                )
                .first()
            )
            if not passed:
                reasons.append(f"Required assessment not passed: {assessment.name}")

        return len(reasons) == 0, reasons


class CertificateService:
    @staticmethod
    def generate_certificate_number(db: Session) -> str:
        while True:
            value = f"KS-{date.today().year}-{secrets.token_hex(4).upper()}"
            if not db.query(Certificate).filter(Certificate.certificate_number == value).first():
                return value

    @staticmethod
    def issue(
        db: Session,
        enrollment: TrainingEnrollment,
        certificate_name: str,
        skill_ids: list[uuid.UUID],
    ) -> Certificate:
        eligible, reasons = CertificateEligibilityService.check(db, enrollment)
        if not eligible:
            raise ValueError("; ".join(reasons))

        existing = db.query(Certificate).filter(Certificate.enrollment_id == enrollment.id).first()
        if existing:
            raise ValueError("A certificate already exists for this enrollment")

        skills = []
        if skill_ids:
            skills = db.query(Skill).filter(Skill.id.in_(skill_ids)).all()
            found = {skill.id for skill in skills}
            missing = [str(skill_id) for skill_id in skill_ids if skill_id not in found]
            if missing:
                raise ValueError("One or more requested skills do not exist")

        certificate = Certificate(
            certificate_number=CertificateService.generate_certificate_number(db),
            learner_id=enrollment.learner_id,
            training_program_id=enrollment.training_program_id,
            enrollment_id=enrollment.id,
            certificate_name=certificate_name,
            issue_date=date.today(),
            status=CertificateStatus.ISSUED,
            verification_code=secrets.token_urlsafe(24),
            skills=skills,
        )
        db.add(certificate)
        db.flush()

        for skill in skills:
            learner_skill = (
                db.query(LearnerSkill)
                .filter(
                    LearnerSkill.learner_id == enrollment.learner_id,
                    LearnerSkill.skill_id == skill.id,
                )
                .first()
            )
            certificate_score = 70
            if learner_skill is None:
                db.add(
                    LearnerSkill(
                        learner_id=enrollment.learner_id,
                        skill_id=skill.id,
                        proficiency_score=certificate_score,
                        proficiency_source=ProficiencySource.CERTIFICATION,
                        verified=True,
                    )
                )
            elif learner_skill.proficiency_score < certificate_score:
                learner_skill.proficiency_score = certificate_score
                learner_skill.proficiency_source = ProficiencySource.CERTIFICATION
                learner_skill.verified = True

        event = CareerEvent(
            learner_id=enrollment.learner_id,
            event_type=CareerEventType.CERTIFICATION,
            title=certificate_name,
            description="Certificate issued after successful completion of training requirements.",
            event_date=certificate.issue_date,
            metadata_={
                "certificate_id": str(certificate.id),
                "certificate_number": certificate.certificate_number,
            },
        )
        db.add(event)
        db.commit()
        db.refresh(certificate)
        return certificate

    @staticmethod
    def serialize(certificate: Certificate) -> dict:
        return {
            "id": certificate.id,
            "certificate_number": certificate.certificate_number,
            "learner_id": certificate.learner_id,
            "training_program_id": certificate.training_program_id,
            "enrollment_id": certificate.enrollment_id,
            "certificate_name": certificate.certificate_name,
            "issue_date": certificate.issue_date,
            "status": certificate.status,
            "verification_code": certificate.verification_code,
            "skill_ids": [skill.id for skill in certificate.skills],
            "created_at": certificate.created_at,
            "updated_at": certificate.updated_at,
        }
