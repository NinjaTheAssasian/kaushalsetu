"""Seed realistic Phase 5 market-demand data for the government dashboard demo.

Safe to run repeatedly against the existing Phase 2-4 demo database.
"""
from __future__ import annotations

import os
import sys
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models import (
    Employer,
    EmploymentVerificationStatus,
    JobPosting,
    LearnerProfile,
    LearnerSkill,
    OutcomeCheckIn,
    OutcomeEmploymentStatus,
    ProficiencySource,
    Skill,
    TrainingProgram,
    TrainingEnrollment,
    EnrollmentStatus,
)


SKILLS = [
    ("Python", "python", "Programming"),
    ("SQL", "sql", "Data"),
    ("Power BI", "power bi", "Data"),
    ("Data Analysis", "data analysis", "Data"),
    ("Data Visualization", "data visualization", "Data"),
    ("Cloud Computing", "cloud computing", "Cloud"),
    ("AWS", "aws", "Cloud"),
    ("Cybersecurity", "cybersecurity", "Security"),
    ("SIEM", "siem", "Security"),
    ("Threat Hunting", "threat hunting", "Security"),
    ("Linux", "linux", "Infrastructure"),
    ("Networking", "networking", "Infrastructure"),
    ("Machine Learning", "machine learning", "AI"),
    ("Communication", "communication", "Professional"),
    ("Project Management", "project management", "Management"),
]

JOB_BLUEPRINTS = [
    ("SOC Analyst", "Cybersecurity", "IT", "Pune", "Maharashtra", ["Linux", "Networking", "SIEM", "Cybersecurity", "Threat Hunting"]),
    ("Cloud Security Associate", "Cloud Security", "IT", "Pune", "Maharashtra", ["AWS", "Cloud Computing", "Linux", "Cybersecurity"]),
    ("Data Analyst", "Data Analytics", "IT", "Mumbai", "Maharashtra", ["SQL", "Python", "Power BI", "Data Analysis"]),
    ("BI Analyst", "Data Analytics", "IT", "Mumbai", "Maharashtra", ["SQL", "Power BI", "Data Visualization"]),
    ("Junior ML Engineer", "AI/ML", "IT", "Bengaluru", "Karnataka", ["Python", "Machine Learning", "SQL", "Communication"]),
    ("Network Support Engineer", "Infrastructure", "IT", "Nagpur", "Maharashtra", ["Networking", "Linux", "Cloud Computing"]),
    ("Cybersecurity Trainee", "Cybersecurity", "IT", "Nagpur", "Maharashtra", ["Networking", "Linux", "Cybersecurity", "SIEM"]),
    ("Digital Operations Analyst", "Operations", "Services", "Nashik", "Maharashtra", ["Data Analysis", "Excel", "Communication"]),
    ("Cloud Support Associate", "Cloud", "IT", "Pune", "Maharashtra", ["Cloud Computing", "AWS", "Linux", "Communication"]),
    ("Security Monitoring Analyst", "Cybersecurity", "IT", "Mumbai", "Maharashtra", ["SIEM", "Linux", "Networking", "Threat Hunting"]),
    ("Data Operations Associate", "Data Analytics", "IT", "Delhi", "Delhi", ["SQL", "Data Analysis", "Communication"]),
    ("Project Coordinator", "Project Management", "Services", "Pune", "Maharashtra", ["Project Management", "Communication", "Data Analysis"]),
]


def ensure_skill(db, name: str, normalized: str, category: str) -> Skill:
    skill = db.query(Skill).filter(Skill.normalized_name == normalized).first()
    if skill:
        return skill
    skill = Skill(name=name, normalized_name=normalized, category=category)
    db.add(skill)
    db.flush()
    return skill


def seed_phase5() -> None:
    db = SessionLocal()
    try:
        # Ensure skills exist.
        skills = {name: ensure_skill(db, name, normalized, category) for name, normalized, category in SKILLS}
        db.commit()

        employers = db.query(Employer).order_by(Employer.organization_name.asc()).all()
        if not employers:
            raise RuntimeError("Employer profiles not found. Run seed_db.py first.")

        programs = db.query(TrainingProgram).order_by(TrainingProgram.created_at.asc()).all()
        if not programs:
            raise RuntimeError("Training programs not found. Run seed_db.py first.")

        # Map program curricula to canonical skills.
        program_skill_sets = [
            ["Python", "SQL", "Data Analysis", "Power BI", "Communication"],
            ["Python", "Linux", "Networking", "Cybersecurity", "SIEM"],
            ["Python", "Machine Learning", "Cloud Computing", "AWS", "Data Visualization"],
        ]
        for idx, program in enumerate(programs):
            program.skills = [skills[name] for name in program_skill_sets[idx % len(program_skill_sets)]]
        db.commit()

        # Populate learner proficiency evidence for deterministic supply analytics.
        learners = db.query(LearnerProfile).order_by(LearnerProfile.created_at.asc()).all()
        skill_rotation = ["Python", "SQL", "Linux", "Networking", "Data Analysis", "Communication", "Cloud Computing", "Machine Learning", "Cybersecurity"]
        for index, learner in enumerate(learners):
            for offset in range(3):
                skill = skills[skill_rotation[(index + offset) % len(skill_rotation)]]
                existing = (
                    db.query(LearnerSkill)
                    .filter(LearnerSkill.learner_id == learner.id, LearnerSkill.skill_id == skill.id)
                    .first()
                )
                if not existing:
                    db.add(
                        LearnerSkill(
                            learner_id=learner.id,
                            skill_id=skill.id,
                            proficiency_score=65 + ((index + offset * 7) % 31),
                            proficiency_source=ProficiencySource.ASSESSMENT,
                            verified=(offset == 0),
                        )
                    )
        db.commit()

        # Create employer-demand data.
        existing_titles = {row[0] for row in db.query(JobPosting.title).all()}
        for idx, blueprint in enumerate(JOB_BLUEPRINTS):
            title, role_family, industry, district, state, skill_names = blueprint
            if title in existing_titles:
                continue
            employer = employers[idx % len(employers)]
            job = JobPosting(
                employer_id=employer.id,
                title=title,
                role_family=role_family,
                industry=industry,
                district=district,
                state=state,
                employment_type="FULL_TIME",
                salary_band="₹3L–₹8L",
                experience_min_years=0,
                is_active=True,
                posted_at=date.today() - timedelta(days=(idx + 1) * 3),
            )
            job.skills = [skills[name] for name in skill_names if name in skills]
            db.add(job)
        db.commit()

        # Add a small but believable set of outcome milestones for the dashboard.
        for idx, learner in enumerate(learners):
            milestone = 3
            existing = (
                db.query(OutcomeCheckIn)
                .filter(OutcomeCheckIn.learner_id == learner.id, OutcomeCheckIn.milestone_months == milestone)
                .first()
            )
            if existing:
                continue
            if idx % 4 == 0:
                status = OutcomeEmploymentStatus.SELF_EMPLOYED
                employer_name = "Independent Digital Services"
                role = "Data & Automation Freelancer"
            elif idx % 4 == 1:
                status = OutcomeEmploymentStatus.EMPLOYED
                employer_name = "TechCorp India"
                role = "Junior Analyst"
            elif idx % 4 == 2:
                status = OutcomeEmploymentStatus.SEEKING_EMPLOYMENT
                employer_name = None
                role = None
            else:
                status = OutcomeEmploymentStatus.EMPLOYED
                employer_name = "BuildCo"
                role = "Operations Analyst"
            db.add(
                OutcomeCheckIn(
                    learner_id=learner.id,
                    milestone_months=milestone,
                    check_in_date=date.today(),
                    employment_status=status,
                    employer_name=employer_name,
                    role_title=role,
                    industry="IT" if idx % 2 == 0 else "Services",
                    district=learner.district,
                    state=learner.state,
                    income_band="₹20k–₹30k" if status in {OutcomeEmploymentStatus.EMPLOYED, OutcomeEmploymentStatus.SELF_EMPLOYED} else None,
                    same_employer=(idx % 3 == 0) if status == OutcomeEmploymentStatus.EMPLOYED else None,
                    training_relevance_score=70 + (idx * 4),
                    using_training_skills=True,
                    skill_gap_notes="Needs stronger cloud exposure" if idx % 2 == 0 else "",
                )
            )
        db.commit()

        print("Phase 5 demo data ready.")
        print(f"Skills: {db.query(Skill).count()}")
        print(f"Active jobs: {db.query(JobPosting).filter(JobPosting.is_active.is_(True)).count()}")
        print(f"Training programs: {db.query(TrainingProgram).count()}")
        print(f"Learners: {db.query(LearnerProfile).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_phase5()
