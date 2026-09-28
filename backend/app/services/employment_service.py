import hashlib
import secrets
import uuid
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import (
    CareerEvent,
    CareerEventType,
    Employer,
    EmployerSkillFeedback,
    EmploymentRecord,
    EmploymentStatus,
    EmploymentRecordStatus,
    EmploymentVerificationStatus,
    LearnerProfile,
    LearnerSkill,
    ProficiencySource,
    OutcomeCheckIn,
    OutcomeVerificationStatus,
    OutcomeEmploymentStatus,
    Skill,
    User,
    EmploymentType,
)


def _hash_code(code: str) -> str:
    # Verification codes are high-entropy random values. HMAC adds protection
    # against offline guessing from a database dump.
    import hmac

    return hmac.new(
        settings.secret_key.encode("utf-8"), code.encode("utf-8"), hashlib.sha256
    ).hexdigest()


class EmploymentService:
    @staticmethod
    def generate_verification_code() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def create_self_reported(
        db: Session,
        learner: LearnerProfile,
        data: dict,
    ) -> tuple[EmploymentRecord, str]:
        # Keep only one active self-reported employment record for the learner.
        active = (
            db.query(EmploymentRecord)
            .filter(
                EmploymentRecord.learner_id == learner.id,
                EmploymentRecord.status == EmploymentRecordStatus.ACTIVE,
            )
            .first()
        )
        if active:
            raise ValueError("An active employment record already exists. End it before creating another one.")

        code = EmploymentService.generate_verification_code()
        record = EmploymentRecord(
            learner_id=learner.id,
            employer_id=None,
            verification_code_hash=_hash_code(code),
            verification_status=EmploymentVerificationStatus.PENDING,
            status=EmploymentRecordStatus.ACTIVE,
            **data,
        )
        db.add(record)
        db.flush()

        learner.current_employment_status = EmploymentStatus.EMPLOYED
        db.add(
            CareerEvent(
                learner_id=learner.id,
                event_type=CareerEventType.EMPLOYMENT_STARTED,
                title=f"Employment reported: {record.role_title}",
                description="Learner reported an employment outcome awaiting employer verification.",
                event_date=record.start_date,
                metadata_={
                    "employment_record_id": str(record.id),
                    "verification_status": record.verification_status.value,
                },
            )
        )
        db.commit()
        db.refresh(record)
        return record, code

    @staticmethod
    def rotate_verification_code(db: Session, record: EmploymentRecord) -> str:
        if record.verification_status == EmploymentVerificationStatus.EMPLOYER_VERIFIED:
            raise ValueError("Employer-verified employment cannot rotate its verification code")
        code = EmploymentService.generate_verification_code()
        record.verification_code_hash = _hash_code(code)
        record.verification_status = EmploymentVerificationStatus.PENDING
        db.commit()
        db.refresh(record)
        return code

    @staticmethod
    def verify(
        db: Session,
        employer: Employer,
        verification_code: str,
    ) -> EmploymentRecord:
        record = (
            db.query(EmploymentRecord)
            .filter(EmploymentRecord.verification_code_hash == _hash_code(verification_code))
            .first()
        )
        if not record:
            raise ValueError("Invalid employment verification code")

        if record.verification_status == EmploymentVerificationStatus.EMPLOYER_VERIFIED:
            if record.employer_id != employer.id:
                raise ValueError("This employment record has already been verified by another employer")
            return record

        if record.verification_status == EmploymentVerificationStatus.REVOKED:
            raise ValueError("This employment record has been revoked")
        if record.status != EmploymentRecordStatus.ACTIVE:
            raise ValueError("Only active employment records can be employer-verified")

        record.employer_id = employer.id
        record.verification_status = EmploymentVerificationStatus.EMPLOYER_VERIFIED
        record.verified_at = datetime.now(timezone.utc)

        learner = db.query(LearnerProfile).filter(LearnerProfile.id == record.learner_id).first()
        if learner:
            learner.current_employment_status = EmploymentStatus.EMPLOYED
            latest_checkin = (
                db.query(OutcomeCheckIn)
                .filter(
                    OutcomeCheckIn.learner_id == learner.id,
                    OutcomeCheckIn.employment_status == OutcomeEmploymentStatus.EMPLOYED,
                )
                .order_by(OutcomeCheckIn.milestone_months.desc())
                .first()
            )
            if latest_checkin:
                latest_checkin.verification_status = OutcomeVerificationStatus.EMPLOYER_VERIFIED
            db.add(
                CareerEvent(
                    learner_id=learner.id,
                    event_type=CareerEventType.EMPLOYMENT_CHANGED,
                    title=f"Employment verified: {record.role_title}",
                    description="Employer verified the learner's reported employment.",
                    event_date=record.start_date,
                    metadata_={
                        "employment_record_id": str(record.id),
                        "employer_id": str(employer.id),
                        "verification_status": record.verification_status.value,
                    },
                )
            )

        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def end_employment(db: Session, record: EmploymentRecord, end_date: date | None = None) -> EmploymentRecord:
        record.status = EmploymentRecordStatus.ENDED
        record.end_date = end_date or date.today()
        learner = record.learner
        if learner:
            learner.current_employment_status = EmploymentStatus.SEEKING_EMPLOYMENT
            db.add(
                CareerEvent(
                    learner_id=learner.id,
                    event_type=CareerEventType.EMPLOYMENT_CHANGED,
                    title=f"Employment ended: {record.role_title}",
                    description="Employment record marked as ended.",
                    event_date=record.end_date,
                    metadata_={"employment_record_id": str(record.id)},
                )
            )
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def upsert_skill_feedback(
        db: Session,
        record: EmploymentRecord,
        employer: Employer,
        skill_id: uuid.UUID,
        rating: int,
        comments: str | None,
    ) -> EmployerSkillFeedback:
        skill = db.query(Skill).filter(Skill.id == skill_id).first()
        if not skill:
            raise ValueError("Skill not found")
        if not 0 <= rating <= 100:
            raise ValueError("rating must be between 0 and 100")
        if record.employer_id != employer.id or record.verification_status != EmploymentVerificationStatus.EMPLOYER_VERIFIED:
            raise ValueError("Employment must be verified by this employer before submitting skill feedback")

        feedback = (
            db.query(EmployerSkillFeedback)
            .filter(
                EmployerSkillFeedback.employment_record_id == record.id,
                EmployerSkillFeedback.skill_id == skill_id,
            )
            .first()
        )
        if feedback is None:
            feedback = EmployerSkillFeedback(
                employment_record_id=record.id,
                employer_id=employer.id,
                skill_id=skill.id,
                rating=rating,
                comments=comments,
            )
            db.add(feedback)
        else:
            feedback.rating = rating
            feedback.comments = comments

        learner_skill = (
            db.query(LearnerSkill)
            .filter(
                LearnerSkill.learner_id == record.learner_id,
                LearnerSkill.skill_id == skill.id,
            )
            .first()
        )
        if learner_skill is None:
            db.add(
                LearnerSkill(
                    learner_id=record.learner_id,
                    skill_id=skill.id,
                    proficiency_score=rating,
                    proficiency_source=ProficiencySource.EMPLOYER,
                    verified=True,
                )
            )
        elif rating >= learner_skill.proficiency_score:
            learner_skill.proficiency_score = rating
            learner_skill.proficiency_source = ProficiencySource.EMPLOYER
            learner_skill.verified = True

        db.commit()
        db.refresh(feedback)
        return feedback
