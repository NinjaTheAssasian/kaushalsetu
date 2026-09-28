import sys
import os
import random
from datetime import date, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models import (
    User, UserRole, LearnerProfile, EmploymentStatus, TrainingProvider,
    Employer, GovernmentAdmin, Skill, TrainingProgram, TrainingEnrollment,
    CareerEvent, CareerEventType, LearnerSkill, ProficiencySource
)
from app.core.security import get_password_hash

def seed_db():
    db = SessionLocal()
    try:
        # Create users
        admin_user = User(email="admin@gov.in", password_hash=get_password_hash("admin123"), role=UserRole.GOVERNMENT_ADMIN)
        provider_user = User(email="provider@training.com", password_hash=get_password_hash("provider123"), role=UserRole.TRAINING_PROVIDER)
        emp1_user = User(email="hr@techcorp.com", password_hash=get_password_hash("emp123"), role=UserRole.EMPLOYER)
        emp2_user = User(email="hiring@buildco.com", password_hash=get_password_hash("emp123"), role=UserRole.EMPLOYER)
        
        learner_users = []
        for i in range(1, 6):
            u = User(email=f"learner{i}@example.com", password_hash=get_password_hash("learner123"), role=UserRole.TRAINEE)
            learner_users.append(u)
            db.add(u)

        db.add_all([admin_user, provider_user, emp1_user, emp2_user])
        db.commit()

        # Profiles
        admin_profile = GovernmentAdmin(user_id=admin_user.id, department="Ministry of Skill Development", jurisdiction="National")
        provider_profile = TrainingProvider(user_id=provider_user.id, organization_name="Skill India Institute", registration_number="TP-001", district="New Delhi", state="Delhi")
        emp1_profile = Employer(user_id=emp1_user.id, organization_name="TechCorp India", industry="IT", registration_number="EMP-001", district="Bangalore", state="Karnataka")
        emp2_profile = Employer(user_id=emp2_user.id, organization_name="BuildCo", industry="Construction", registration_number="EMP-002", district="Mumbai", state="Maharashtra")
        db.add_all([admin_profile, provider_profile, emp1_profile, emp2_profile])
        
        learner_profiles = []
        for i, u in enumerate(learner_users):
            lp = LearnerProfile(
                user_id=u.id,
                first_name=f"Learner{i+1}",
                last_name="Singh",
                date_of_birth=date(1995, 1, 1) + timedelta(days=i*100),
                education_level="B.Tech" if i%2==0 else "High School",
                district="Delhi",
                state="Delhi",
                current_employment_status=EmploymentStatus.NOT_CURRENTLY_WORKING if i%2==0 else EmploymentStatus.EMPLOYED
            )
            learner_profiles.append(lp)
            db.add(lp)
        db.commit()

        # Skills
        skill_names = ["Python", "Java", "Welding", "Carpentry", "Data Analysis", "Communication", "Project Management", "Digital Marketing", "Machine Learning", "Cloud Computing"]
        skills = []
        for name in skill_names:
            s = Skill(name=name, normalized_name=name.lower(), category="IT" if "Data" in name or "Python" in name or "Cloud" in name else "General")
            skills.append(s)
            db.add(s)
        db.commit()

        # Training Programs
        programs = []
        for i in range(3):
            tp = TrainingProgram(
                provider_id=provider_profile.id,
                name=f"Advanced Training {i+1}",
                description="Comprehensive training program.",
                category="IT",
                duration_hours=120,
                start_date=date.today(),
                capacity=30
            )
            programs.append(tp)
            db.add(tp)
        db.commit()

        # Phase 3A: Assessments
        from app.models import Assessment, AssessmentType, AssessmentResult, AttendanceRecord, AttendanceStatus
        
        assessments = []
        for i, tp in enumerate(programs):
            # Midterm Quiz
            a1 = Assessment(
                training_program_id=tp.id, name=f"Midterm Quiz for {tp.name}", assessment_type=AssessmentType.QUIZ,
                max_score=50, passing_score=25, assessment_date=date.today() - timedelta(days=10)
            )
            # Final Practical
            a2 = Assessment(
                training_program_id=tp.id, name=f"Final Practical for {tp.name}", assessment_type=AssessmentType.PRACTICAL,
                max_score=100, passing_score=60, assessment_date=date.today()
            )
            db.add_all([a1, a2])
            assessments.extend([a1, a2])
        db.commit()

        # Enrollments & Phase 3A Data
        for i, lp in enumerate(learner_profiles):
            for j in range(2): # Each learner gets 2 enrollments
                tp = programs[(i+j)%3]
                enr = TrainingEnrollment(
                    learner_id=lp.id,
                    training_program_id=tp.id,
                    attendance_percentage=random.randint(70, 100),
                    completion_percentage=random.randint(50, 100)
                )
                db.add(enr)
                db.commit()
                
                # Learner Skills
                ls = LearnerSkill(
                    learner_id=lp.id,
                    skill_id=skills[(i+j)%10].id,
                    proficiency_score=random.randint(60, 100),
                    proficiency_source=ProficiencySource.TRAINING
                )
                db.add(ls)
                
                # Career Events
                ce = CareerEvent(
                    learner_id=lp.id,
                    event_type=CareerEventType.ENROLLMENT,
                    title="Enrolled in Program",
                    event_date=date.today()
                )
                db.add(ce)
                
                # Phase 3A: Attendance Records (5 days)
                for day in range(5):
                    att = AttendanceRecord(
                        enrollment_id=enr.id,
                        attendance_date=date.today() - timedelta(days=day),
                        status=random.choice([AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.ABSENT]),
                        hours_attended=8.0
                    )
                    db.add(att)
                
                # Phase 3A: Assessment Results
                prog_assessments = [a for a in assessments if a.training_program_id == tp.id]
                for a in prog_assessments:
                    score = random.randint(int(a.passing_score - 10), int(a.max_score))
                    score = max(0, score) # prevent negative
                    percentage = (score / a.max_score) * 100
                    passed = percentage >= a.passing_score
                    ar = AssessmentResult(
                        assessment_id=a.id,
                        learner_id=lp.id,
                        attempt_number=1,
                        score=score,
                        percentage=percentage,
                        passed=passed,
                        remarks="Good job" if passed else "Needs improvement"
                    )
                    db.add(ar)

        db.commit()
        print("Database seeded successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
