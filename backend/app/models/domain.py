import uuid
from datetime import datetime, date
from typing import List, Optional
import enum

from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean, Date, JSON, Float, Enum, UniqueConstraint, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import Base, uuid_gen, utc_now

class UserRole(str, enum.Enum):
    TRAINEE = "TRAINEE"
    TRAINING_PROVIDER = "TRAINING_PROVIDER"
    EMPLOYER = "EMPLOYER"
    GOVERNMENT_ADMIN = "GOVERNMENT_ADMIN"


# Association tables are declared before ORM mapper configuration.
certificate_skills = Table(
    "certificate_skills",
    Base.metadata,
    Column("certificate_id", ForeignKey("certificates.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

training_program_skills = Table(
    "training_program_skills",
    Base.metadata,
    Column("training_program_id", ForeignKey("training_programs.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

job_posting_skills = Table(
    "job_posting_skills",
    Base.metadata,
    Column("job_posting_id", ForeignKey("job_postings.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    learner_profile: Mapped["LearnerProfile"] = relationship(back_populates="user", uselist=False)
    training_provider: Mapped["TrainingProvider"] = relationship(back_populates="user", uselist=False)
    employer: Mapped["Employer"] = relationship(back_populates="user", uselist=False)
    government_admin: Mapped["GovernmentAdmin"] = relationship(back_populates="user", uselist=False)
    apaar_identity: Mapped["ApaarIdentity"] = relationship(back_populates="user", uselist=False)

class EmploymentStatus(str, enum.Enum):
    EMPLOYED = "EMPLOYED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    FREELANCER = "FREELANCER"
    ENTREPRENEUR = "ENTREPRENEUR"
    APPRENTICESHIP = "APPRENTICESHIP"
    HIGHER_STUDIES = "HIGHER_STUDIES"
    SEEKING_EMPLOYMENT = "SEEKING_EMPLOYMENT"
    NOT_CURRENTLY_WORKING = "NOT_CURRENTLY_WORKING"

class LearnerProfile(Base):
    __tablename__ = "learner_profiles"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    date_of_birth: Mapped[date] = mapped_column(Date)
    education_level: Mapped[str] = mapped_column(String)
    institution: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    district: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    gender: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    current_employment_status: Mapped[EmploymentStatus] = mapped_column(Enum(EmploymentStatus))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="learner_profile")
    enrollments: Mapped[List["TrainingEnrollment"]] = relationship(back_populates="learner")
    skills: Mapped[List["LearnerSkill"]] = relationship(back_populates="learner")
    career_events: Mapped[List["CareerEvent"]] = relationship(back_populates="learner")
    certificates: Mapped[List["Certificate"]] = relationship(back_populates="learner")
    outcome_checkins: Mapped[List["OutcomeCheckIn"]] = relationship(back_populates="learner")
    employment_records: Mapped[List["EmploymentRecord"]] = relationship(back_populates="learner")

class VerificationStatus(str, enum.Enum):
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"

class ApaarIdentity(Base):
    __tablename__ = "apaar_identities"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    masked_apaar_id: Mapped[str] = mapped_column(String)
    apaar_hash: Mapped[str] = mapped_column(String, unique=True, index=True)
    verification_status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus), default=VerificationStatus.UNVERIFIED)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="apaar_identity")

class TrainingProvider(Base):
    __tablename__ = "training_providers"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    organization_name: Mapped[str] = mapped_column(String)
    registration_number: Mapped[str] = mapped_column(String)
    district: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="training_provider")
    programs: Mapped[List["TrainingProgram"]] = relationship(back_populates="provider")

class Employer(Base):
    __tablename__ = "employers"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    organization_name: Mapped[str] = mapped_column(String)
    industry: Mapped[str] = mapped_column(String)
    registration_number: Mapped[str] = mapped_column(String)
    district: Mapped[str] = mapped_column(String)
    state: Mapped[str] = mapped_column(String)
    website: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="employer")
    employment_records: Mapped[List["EmploymentRecord"]] = relationship(back_populates="employer")
    skill_feedback: Mapped[List["EmployerSkillFeedback"]] = relationship(back_populates="employer")
    job_postings: Mapped[List["JobPosting"]] = relationship(back_populates="employer")

class GovernmentAdmin(Base):
    __tablename__ = "government_admins"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    department: Mapped[str] = mapped_column(String)
    jurisdiction: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="government_admin")

class TrainingProgram(Base):
    __tablename__ = "training_programs"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_providers.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)
    duration_hours: Mapped[int] = mapped_column(Integer)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    capacity: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    provider: Mapped["TrainingProvider"] = relationship(back_populates="programs")
    enrollments: Mapped[List["TrainingEnrollment"]] = relationship(back_populates="training_program")
    certificates: Mapped[List["Certificate"]] = relationship(back_populates="training_program")
    skills: Mapped[List["Skill"]] = relationship(
        secondary=training_program_skills,
        back_populates="training_programs",
    )

class EnrollmentStatus(str, enum.Enum):
    ENROLLED = "ENROLLED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DROPPED = "DROPPED"
    WITHDRAWN = "WITHDRAWN"

class TrainingEnrollment(Base):
    __tablename__ = "training_enrollments"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"), index=True)
    training_program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_programs.id"), index=True)
    enrollment_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    completion_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[EnrollmentStatus] = mapped_column(Enum(EnrollmentStatus), default=EnrollmentStatus.ENROLLED)
    attendance_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    completion_percentage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    learner: Mapped["LearnerProfile"] = relationship(back_populates="enrollments")
    training_program: Mapped["TrainingProgram"] = relationship(back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint('learner_id', 'training_program_id', name='uq_learner_training_program'),
    )

class Skill(Base):
    __tablename__ = "skills"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    name: Mapped[str] = mapped_column(String)
    normalized_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    category: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    certificates: Mapped[List["Certificate"]] = relationship(
        secondary=certificate_skills,
        back_populates="skills",
    )
    training_programs: Mapped[List["TrainingProgram"]] = relationship(
        secondary=training_program_skills,
        back_populates="skills",
    )
    job_postings: Mapped[List["JobPosting"]] = relationship(
        secondary=job_posting_skills,
        back_populates="skills",
    )

class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    employer_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("employers.id", ondelete="SET NULL"), index=True, nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    role_family: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    industry: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    state: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    employment_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    salary_band: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    experience_min_years: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    posted_at: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    closing_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    employer: Mapped[Optional["Employer"]] = relationship(back_populates="job_postings")
    skills: Mapped[List["Skill"]] = relationship(
        secondary=job_posting_skills,
        back_populates="job_postings",
    )


class ProficiencySource(str, enum.Enum):
    TRAINING = "TRAINING"
    ASSESSMENT = "ASSESSMENT"
    CERTIFICATION = "CERTIFICATION"
    EMPLOYER = "EMPLOYER"
    LEARNER = "LEARNER"
    AI = "AI"

class LearnerSkill(Base):
    __tablename__ = "learner_skills"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"), index=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), index=True)
    proficiency_score: Mapped[int] = mapped_column(Integer) # 0-100
    proficiency_source: Mapped[ProficiencySource] = mapped_column(Enum(ProficiencySource))
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    learner: Mapped["LearnerProfile"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship()

    __table_args__ = (
        UniqueConstraint('learner_id', 'skill_id', name='uq_learner_skill'),
    )

class CareerEventType(str, enum.Enum):
    ENROLLMENT = "ENROLLMENT"
    TRAINING_COMPLETED = "TRAINING_COMPLETED"
    CERTIFICATION = "CERTIFICATION"
    EMPLOYMENT_STARTED = "EMPLOYMENT_STARTED"
    EMPLOYMENT_CHANGED = "EMPLOYMENT_CHANGED"
    PROMOTION = "PROMOTION"
    SALARY_CHANGE = "SALARY_CHANGE"
    SELF_EMPLOYMENT_STARTED = "SELF_EMPLOYMENT_STARTED"
    HIGHER_STUDIES = "HIGHER_STUDIES"
    OTHER = "OTHER"

class CareerEvent(Base):
    __tablename__ = "career_events"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"), index=True)
    event_type: Mapped[CareerEventType] = mapped_column(Enum(CareerEventType))
    title: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    event_date: Mapped[date] = mapped_column(Date)
    metadata_: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    learner: Mapped["LearnerProfile"] = relationship(back_populates="career_events")

# PHASE 3A Additions

class AttendanceStatus(str, enum.Enum):
    PRESENT = "PRESENT"
    ABSENT = "ABSENT"
    LEAVE = "LEAVE"

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_enrollments.id"), index=True)
    attendance_date: Mapped[date] = mapped_column(Date)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus))
    hours_attended: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    enrollment: Mapped["TrainingEnrollment"] = relationship()

    __table_args__ = (
        UniqueConstraint('enrollment_id', 'attendance_date', name='uq_enrollment_attendance_date'),
    )

class AssessmentType(str, enum.Enum):
    QUIZ = "QUIZ"
    PRACTICAL = "PRACTICAL"
    PROJECT = "PROJECT"
    FINAL = "FINAL"
    OTHER = "OTHER"

class Assessment(Base):
    __tablename__ = "assessments"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    training_program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_programs.id"), index=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assessment_type: Mapped[AssessmentType] = mapped_column(Enum(AssessmentType))
    max_score: Mapped[float] = mapped_column(Float)
    passing_score: Mapped[float] = mapped_column(Float)
    assessment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    training_program: Mapped["TrainingProgram"] = relationship()
    results: Mapped[List["AssessmentResult"]] = relationship(back_populates="assessment")

class AssessmentResult(Base):
    __tablename__ = "assessment_results"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id"), index=True)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[float] = mapped_column(Float)
    percentage: Mapped[float] = mapped_column(Float)
    passed: Mapped[bool] = mapped_column(Boolean)
    remarks: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    assessment: Mapped["Assessment"] = relationship(back_populates="results")
    learner: Mapped["LearnerProfile"] = relationship()

    __table_args__ = (
        UniqueConstraint('assessment_id', 'learner_id', 'attempt_number', name='uq_assessment_learner_attempt'),
    )


# PHASE 3B/3C Additions

class CertificateStatus(str, enum.Enum):
    ISSUED = "ISSUED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class OutcomeVerificationStatus(str, enum.Enum):
    SELF_REPORTED = "SELF_REPORTED"
    EMPLOYER_VERIFIED = "EMPLOYER_VERIFIED"
    DOCUMENT_VERIFIED = "DOCUMENT_VERIFIED"


class OutcomeEmploymentStatus(str, enum.Enum):
    EMPLOYED = "EMPLOYED"
    SELF_EMPLOYED = "SELF_EMPLOYED"
    FREELANCER = "FREELANCER"
    ENTREPRENEUR = "ENTREPRENEUR"
    APPRENTICESHIP = "APPRENTICESHIP"
    HIGHER_STUDIES = "HIGHER_STUDIES"
    SEEKING_EMPLOYMENT = "SEEKING_EMPLOYMENT"
    NOT_CURRENTLY_WORKING = "NOT_CURRENTLY_WORKING"


class Certificate(Base):
    __tablename__ = "certificates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    certificate_number: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"), index=True)
    training_program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_programs.id"), index=True)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_enrollments.id"), unique=True, index=True)
    certificate_name: Mapped[str] = mapped_column(String(255))
    issue_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    status: Mapped[CertificateStatus] = mapped_column(Enum(CertificateStatus), default=CertificateStatus.ISSUED)
    verification_code: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    learner: Mapped["LearnerProfile"] = relationship(back_populates="certificates")
    training_program: Mapped["TrainingProgram"] = relationship(back_populates="certificates")
    enrollment: Mapped["TrainingEnrollment"] = relationship()
    skills: Mapped[List["Skill"]] = relationship(
        secondary=certificate_skills,
        back_populates="certificates",
    )


class OutcomeCheckIn(Base):
    __tablename__ = "outcome_checkins"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id"), index=True)
    milestone_months: Mapped[int] = mapped_column(Integer)
    check_in_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    employment_status: Mapped[OutcomeEmploymentStatus] = mapped_column(Enum(OutcomeEmploymentStatus))
    employer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    income_band: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    same_employer: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    training_relevance_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    using_training_skills: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    skill_gap_notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    verification_status: Mapped[OutcomeVerificationStatus] = mapped_column(
        Enum(OutcomeVerificationStatus), default=OutcomeVerificationStatus.SELF_REPORTED
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    learner: Mapped["LearnerProfile"] = relationship(back_populates="outcome_checkins")

    __table_args__ = (
        UniqueConstraint("learner_id", "milestone_months", name="uq_learner_outcome_milestone"),
    )


# PHASE 4: Employer Integration + Employment Verification

class EmploymentType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    APPRENTICESHIP = "APPRENTICESHIP"


class EmploymentRecordStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class EmploymentVerificationStatus(str, enum.Enum):
    SELF_REPORTED = "SELF_REPORTED"
    PENDING = "PENDING"
    EMPLOYER_VERIFIED = "EMPLOYER_VERIFIED"
    REVOKED = "REVOKED"


class EmploymentRecord(Base):
    __tablename__ = "employment_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    learner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("learner_profiles.id", ondelete="CASCADE"), index=True)
    employer_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("employers.id", ondelete="SET NULL"), index=True, nullable=True
    )
    role_title: Mapped[str] = mapped_column(String(255))
    reported_employer_name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[EmploymentType] = mapped_column(Enum(EmploymentType))
    district: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    salary_band: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[EmploymentRecordStatus] = mapped_column(
        Enum(EmploymentRecordStatus), default=EmploymentRecordStatus.ACTIVE
    )
    verification_status: Mapped[EmploymentVerificationStatus] = mapped_column(
        Enum(EmploymentVerificationStatus), default=EmploymentVerificationStatus.SELF_REPORTED
    )
    verification_code_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    learner: Mapped["LearnerProfile"] = relationship(back_populates="employment_records")
    employer: Mapped[Optional["Employer"]] = relationship(back_populates="employment_records")
    skill_feedback: Mapped[List["EmployerSkillFeedback"]] = relationship(
        back_populates="employment_record", cascade="all, delete-orphan"
    )


class EmployerSkillFeedback(Base):
    __tablename__ = "employer_skill_feedback"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid_gen)
    employment_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employment_records.id", ondelete="CASCADE"), index=True
    )
    employer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("employers.id", ondelete="CASCADE"), index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer)
    comments: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    employment_record: Mapped["EmploymentRecord"] = relationship(back_populates="skill_feedback")
    employer: Mapped["Employer"] = relationship(back_populates="skill_feedback")
    skill: Mapped["Skill"] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "employment_record_id", "skill_id",
            name="uq_employment_skill_feedback",
        ),
    )
