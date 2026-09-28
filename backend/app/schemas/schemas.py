from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
from datetime import datetime, date

from app.models.domain import (
    UserRole,
    VerificationStatus,
    EmploymentStatus,
    EnrollmentStatus,
    ProficiencySource,
    CareerEventType,
    AttendanceStatus,
    AssessmentType,
    CertificateStatus, OutcomeVerificationStatus, OutcomeEmploymentStatus,
    EmploymentType, EmploymentRecordStatus, EmploymentVerificationStatus
)

class UserBase(BaseModel):
    email: EmailStr
    role: UserRole

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# Apaar
class ApaarVerifyRequest(BaseModel):
    apaar_id: str

class ApaarStatusResponse(BaseModel):
    masked_apaar_id: str
    verification_status: VerificationStatus

class ApaarIdentityResponse(ApaarStatusResponse):
    id: uuid.UUID
    verified_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True

# Learner
class LearnerProfileBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    education_level: str
    institution: Optional[str] = None
    district: str
    state: str
    gender: Optional[str] = None
    current_employment_status: EmploymentStatus

class LearnerProfileCreate(LearnerProfileBase):
    pass

class LearnerProfileUpdate(LearnerProfileBase):
    pass

class LearnerProfileResponse(LearnerProfileBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Training Provider
class TrainingProviderBase(BaseModel):
    organization_name: str
    registration_number: str
    district: str
    state: str
    website: Optional[str] = None

class TrainingProviderResponse(TrainingProviderBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Employer
class EmployerBase(BaseModel):
    organization_name: str
    industry: str
    registration_number: str
    district: str
    state: str
    website: Optional[str] = None

class EmployerResponse(EmployerBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Training Program
class TrainingProgramBase(BaseModel):
    name: str
    description: str
    category: str
    duration_hours: int
    start_date: date
    end_date: Optional[date] = None
    capacity: int
    is_active: bool = True

class TrainingProgramCreate(TrainingProgramBase):
    pass

class TrainingProgramResponse(TrainingProgramBase):
    id: uuid.UUID
    provider_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Training Enrollment
class TrainingEnrollmentCreate(BaseModel):
    training_program_id: uuid.UUID

class TrainingEnrollmentResponse(BaseModel):
    id: uuid.UUID
    learner_id: uuid.UUID
    training_program_id: uuid.UUID
    enrollment_date: date
    completion_date: Optional[date] = None
    status: EnrollmentStatus
    attendance_percentage: Optional[float] = None
    completion_percentage: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Skill
class SkillBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None

class SkillCreate(SkillBase):
    pass

class SkillResponse(SkillBase):
    id: uuid.UUID
    normalized_name: str
    created_at: datetime

    class Config:
        from_attributes = True

# Learner Skill
class LearnerSkillCreate(BaseModel):
    skill_id: uuid.UUID
    proficiency_score: int
    proficiency_source: ProficiencySource = ProficiencySource.LEARNER

class LearnerSkillResponse(BaseModel):
    id: uuid.UUID
    learner_id: uuid.UUID
    skill_id: uuid.UUID
    proficiency_score: int
    proficiency_source: ProficiencySource
    verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Career Event
class CareerEventCreate(BaseModel):
    event_type: CareerEventType
    title: str
    description: Optional[str] = None
    event_date: date
    metadata_: Optional[dict] = None

class CareerEventResponse(BaseModel):
    id: uuid.UUID
    learner_id: uuid.UUID
    event_type: CareerEventType
    title: str
    description: Optional[str] = None
    event_date: date
    metadata_: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

# Attendance Record
class AttendanceRecordCreate(BaseModel):
    attendance_date: date
    status: AttendanceStatus
    hours_attended: Optional[float] = None
    remarks: Optional[str] = None

class AttendanceRecordResponse(BaseModel):
    id: uuid.UUID
    enrollment_id: uuid.UUID
    attendance_date: date
    status: AttendanceStatus
    hours_attended: Optional[float] = None
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Assessment
class AssessmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    assessment_type: AssessmentType
    max_score: float
    passing_score: float
    assessment_date: Optional[date] = None

class AssessmentResponse(BaseModel):
    id: uuid.UUID
    training_program_id: uuid.UUID
    name: str
    description: Optional[str] = None
    assessment_type: AssessmentType
    max_score: float
    passing_score: float
    assessment_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Assessment Result
class AssessmentResultCreate(BaseModel):
    learner_id: uuid.UUID
    score: float
    remarks: Optional[str] = None
    attempt_number: int = 1

class AssessmentResultResponse(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    learner_id: uuid.UUID
    attempt_number: int
    score: float
    percentage: float
    passed: bool
    remarks: Optional[str] = None
    assessed_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Certificates
class CertificateCreate(BaseModel):
    enrollment_id: uuid.UUID
    certificate_name: Optional[str] = None
    skill_ids: List[uuid.UUID] = []

class CertificateIssueRequest(BaseModel):
    certificate_name: Optional[str] = None
    skill_ids: List[uuid.UUID] = []

class CertificateEligibilityResponse(BaseModel):
    eligible: bool
    reasons: List[str] = []

class CertificateResponse(BaseModel):
    id: uuid.UUID
    certificate_number: str
    learner_id: uuid.UUID
    training_program_id: uuid.UUID
    enrollment_id: uuid.UUID
    certificate_name: str
    issue_date: date
    status: CertificateStatus
    verification_code: str
    skill_ids: List[uuid.UUID] = []
    created_at: datetime
    updated_at: datetime

class CertificateVerificationResponse(BaseModel):
    valid: bool
    certificate_number: Optional[str] = None
    certificate_name: Optional[str] = None
    issued_on: Optional[date] = None
    status: Optional[CertificateStatus] = None
    program_name: Optional[str] = None
    skills: List[str] = []

# Longitudinal outcome check-ins
class OutcomeCheckInCreate(BaseModel):
    milestone_months: int
    check_in_date: Optional[date] = None
    employment_status: OutcomeEmploymentStatus
    employer_name: Optional[str] = None
    role_title: Optional[str] = None
    industry: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    income_band: Optional[str] = None
    same_employer: Optional[bool] = None
    training_relevance_score: Optional[int] = None
    using_training_skills: Optional[bool] = None
    skill_gap_notes: Optional[str] = None

class OutcomeCheckInResponse(BaseModel):
    id: uuid.UUID
    learner_id: uuid.UUID
    milestone_months: int
    check_in_date: date
    employment_status: OutcomeEmploymentStatus
    employer_name: Optional[str] = None
    role_title: Optional[str] = None
    industry: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    income_band: Optional[str] = None
    same_employer: Optional[bool] = None
    training_relevance_score: Optional[int] = None
    using_training_skills: Optional[bool] = None
    skill_gap_notes: Optional[str] = None
    verification_status: OutcomeVerificationStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Enrollment progress
class TrainingEnrollmentProgressUpdate(BaseModel):
    status: Optional[EnrollmentStatus] = None
    completion_percentage: Optional[float] = None
    completion_date: Optional[date] = None

# Combined longitudinal timeline
class TimelineItem(BaseModel):
    event_type: str
    event_date: date
    title: str
    description: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[dict] = None


# Phase 4: Employer integration + employment verification
class EmploymentRecordCreate(BaseModel):
    role_title: str
    reported_employer_name: str
    industry: Optional[str] = None
    employment_type: EmploymentType
    district: Optional[str] = None
    state: Optional[str] = None
    start_date: date
    salary_band: Optional[str] = None

class EmploymentRecordUpdate(BaseModel):
    role_title: Optional[str] = None
    industry: Optional[str] = None
    employment_type: Optional[EmploymentType] = None
    district: Optional[str] = None
    state: Optional[str] = None
    salary_band: Optional[str] = None
    end_date: Optional[date] = None
    status: Optional[EmploymentRecordStatus] = None

class EmploymentRecordResponse(BaseModel):
    id: uuid.UUID
    learner_id: uuid.UUID
    employer_id: Optional[uuid.UUID] = None
    employer_name: Optional[str] = None
    role_title: str
    reported_employer_name: str
    industry: Optional[str] = None
    employment_type: EmploymentType
    district: Optional[str] = None
    state: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    salary_band: Optional[str] = None
    status: EmploymentRecordStatus
    verification_status: EmploymentVerificationStatus
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class EmploymentRecordCreateResponse(EmploymentRecordResponse):
    verification_code: str

class EmploymentVerificationRequest(BaseModel):
    verification_code: str

class EmploymentVerificationResponse(BaseModel):
    id: uuid.UUID
    status: EmploymentVerificationStatus
    employer_name: Optional[str] = None
    role_title: str
    start_date: date
    message: str

class EmployerSkillFeedbackCreate(BaseModel):
    skill_id: uuid.UUID
    rating: int
    comments: Optional[str] = None

class EmployerSkillFeedbackResponse(BaseModel):
    id: uuid.UUID
    employment_record_id: uuid.UUID
    employer_id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: Optional[str] = None
    rating: int
    comments: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class EmploymentFeedbackSummary(BaseModel):
    employment_record_id: uuid.UUID
    feedback_count: int
    average_rating: Optional[float] = None
    feedback: List[EmployerSkillFeedbackResponse] = []

# Phase 5: job-market intelligence
class JobPostingCreate(BaseModel):
    title: str
    role_family: str
    industry: str
    district: str
    state: str
    employment_type: Optional[str] = None
    salary_band: Optional[str] = None
    experience_min_years: int = 0
    is_active: bool = True
    posted_at: Optional[date] = None
    closing_date: Optional[date] = None
    skill_ids: List[uuid.UUID] = []

class JobPostingResponse(BaseModel):
    id: uuid.UUID
    employer_id: Optional[uuid.UUID]
    title: str
    role_family: str
    industry: str
    district: str
    state: str
    employment_type: Optional[str]
    salary_band: Optional[str]
    experience_min_years: int
    is_active: bool
    posted_at: date
    closing_date: Optional[date]
    skill_ids: List[uuid.UUID] = []
    skill_names: List[str] = []
    created_at: datetime
    updated_at: datetime
