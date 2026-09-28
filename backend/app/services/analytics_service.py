from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    AssessmentResult,
    Certificate,
    CertificateStatus,
    EmploymentRecord,
    EmploymentVerificationStatus,
    EnrollmentStatus,
    LearnerProfile,
    LearnerSkill,
    JobPosting,
    OutcomeCheckIn,
    OutcomeEmploymentStatus,
    Skill,
    TrainingEnrollment,
    TrainingProgram,
)


EMPLOYED_STATUSES = {
    OutcomeEmploymentStatus.EMPLOYED,
    OutcomeEmploymentStatus.SELF_EMPLOYED,
    OutcomeEmploymentStatus.FREELANCER,
    OutcomeEmploymentStatus.ENTREPRENEUR,
    OutcomeEmploymentStatus.APPRENTICESHIP,
}


class AnalyticsService:
    """Deterministic government analytics. Gemini only interprets these facts."""

    @staticmethod
    def overview(db: Session) -> dict[str, Any]:
        total_learners = db.query(func.count(LearnerProfile.id)).scalar() or 0
        total_enrollments = db.query(func.count(TrainingEnrollment.id)).scalar() or 0
        completed_enrollments = (
            db.query(func.count(TrainingEnrollment.id))
            .filter(TrainingEnrollment.status == EnrollmentStatus.COMPLETED)
            .scalar()
            or 0
        )
        total_certificates = (
            db.query(func.count(Certificate.id))
            .filter(Certificate.status == CertificateStatus.ISSUED)
            .scalar()
            or 0
        )
        verified_employment_learners = (
            db.query(func.count(func.distinct(EmploymentRecord.learner_id)))
            .filter(EmploymentRecord.verification_status == EmploymentVerificationStatus.EMPLOYER_VERIFIED)
            .scalar()
            or 0
        )
        trained_learners = db.query(func.count(func.distinct(TrainingEnrollment.learner_id))).scalar() or 0

        milestone_rates = {}
        retention_rates = {}
        for months in (3, 6, 12):
            rows = db.query(OutcomeCheckIn).filter(OutcomeCheckIn.milestone_months == months).all()
            employed = sum(1 for row in rows if row.employment_status in EMPLOYED_STATUSES)
            same_employer = sum(1 for row in rows if row.employment_status in EMPLOYED_STATUSES and row.same_employer)
            milestone_rates[str(months)] = round((employed / len(rows) * 100), 1) if rows else 0.0
            retention_rates[str(months)] = round((same_employer / employed * 100), 1) if employed else 0.0

        relevance_values = [
            value
            for (value,) in db.query(OutcomeCheckIn.training_relevance_score)
            .filter(OutcomeCheckIn.training_relevance_score.is_not(None))
            .all()
        ]
        avg_relevance = round(sum(relevance_values) / len(relevance_values), 1) if relevance_values else 0.0

        self_employed = (
            db.query(func.count(func.distinct(OutcomeCheckIn.learner_id)))
            .filter(
                OutcomeCheckIn.employment_status.in_([
                    OutcomeEmploymentStatus.SELF_EMPLOYED,
                    OutcomeEmploymentStatus.FREELANCER,
                    OutcomeEmploymentStatus.ENTREPRENEUR,
                ])
            )
            .scalar()
            or 0
        )

        return {
            "total_learners": total_learners,
            "total_enrollments": total_enrollments,
            "completed_enrollments": completed_enrollments,
            "completion_rate": round((completed_enrollments / total_enrollments * 100), 1) if total_enrollments else 0.0,
            "certificates_issued": total_certificates,
            "trained_learners": trained_learners,
            "verified_employment_learners": verified_employment_learners,
            "employment_rate": round((verified_employment_learners / trained_learners * 100), 1) if trained_learners else 0.0,
            "self_employed_learners": self_employed,
            "milestone_employment_rates": milestone_rates,
            "retention_rates": retention_rates,
            "average_training_relevance": avg_relevance,
        }

    @staticmethod
    def skill_supply_demand(db: Session) -> list[dict[str, Any]]:
        skills = db.query(Skill).order_by(Skill.name.asc()).all()
        supply_scores: dict[str, list[int]] = defaultdict(list)
        for learner_skill in db.query(LearnerSkill).all():
            if learner_skill.skill:
                supply_scores[learner_skill.skill.id.hex].append(learner_skill.proficiency_score)

        demand: Counter[str] = Counter()
        for posting in db.query(JobPosting).filter(JobPosting.is_active.is_(True)).all():
            for skill in posting.skills:
                demand[skill.id.hex] += 1

        curriculum: Counter[str] = Counter()
        for program in db.query(TrainingProgram).all():
            for skill in program.skills:
                curriculum[skill.id.hex] += 1

        rows: list[dict[str, Any]] = []
        for skill in skills:
            scores = supply_scores.get(skill.id.hex, [])
            supply_count = len([score for score in scores if score >= 60])
            avg_proficiency = round(sum(scores) / len(scores), 1) if scores else 0.0
            demand_count = demand.get(skill.id.hex, 0)
            gap_count = max(demand_count - supply_count, 0)
            ratio = round(demand_count / max(supply_count, 1), 2)
            if demand_count >= 5 and supply_count == 0:
                priority = "CRITICAL"
            elif ratio >= 2:
                priority = "HIGH"
            elif ratio >= 1:
                priority = "MEDIUM"
            else:
                priority = "LOW"
            rows.append({
                "skill_id": str(skill.id),
                "skill": skill.name,
                "category": skill.category,
                "trained_learners": supply_count,
                "avg_proficiency": avg_proficiency,
                "job_demand": demand_count,
                "demand_supply_ratio": ratio,
                "gap": gap_count,
                "training_program_coverage": curriculum.get(skill.id.hex, 0),
                "priority": priority,
            })
        rows.sort(key=lambda row: (-(row["job_demand"]), -(row["gap"]), row["skill"]))
        return rows

    @staticmethod
    def training_effectiveness(db: Session) -> list[dict[str, Any]]:
        programs = db.query(TrainingProgram).order_by(TrainingProgram.name.asc()).all()
        verified_learner_ids = {
            row[0]
            for row in db.query(EmploymentRecord.learner_id)
            .filter(EmploymentRecord.verification_status == EmploymentVerificationStatus.EMPLOYER_VERIFIED)
            .distinct()
            .all()
        }
        rows: list[dict[str, Any]] = []
        for program in programs:
            enrollments = db.query(TrainingEnrollment).filter(TrainingEnrollment.training_program_id == program.id).all()
            total = len(enrollments)
            completed = sum(1 for enrollment in enrollments if enrollment.status == EnrollmentStatus.COMPLETED)
            learner_ids = {enrollment.learner_id for enrollment in enrollments}
            certified = (
                db.query(func.count(Certificate.id))
                .filter(Certificate.training_program_id == program.id, Certificate.status == CertificateStatus.ISSUED)
                .scalar()
                or 0
            )
            employed = len(learner_ids.intersection(verified_learner_ids))
            assessment_rows = (
                db.query(AssessmentResult)
                .join(AssessmentResult.assessment)
                .filter(AssessmentResult.learner_id.in_(learner_ids))
                .all()
                if learner_ids else []
            )
            avg_assessment = round(
                sum(row.percentage for row in assessment_rows) / len(assessment_rows), 1
            ) if assessment_rows else 0.0
            rows.append({
                "program_id": str(program.id),
                "program": program.name,
                "category": program.category,
                "enrolled": total,
                "completed": completed,
                "completion_rate": round(completed / total * 100, 1) if total else 0.0,
                "certified": certified,
                "certification_rate": round(certified / completed * 100, 1) if completed else 0.0,
                "verified_employed": employed,
                "employment_rate": round(employed / completed * 100, 1) if completed else 0.0,
                "avg_assessment_score": avg_assessment,
                "skills_covered": [skill.name for skill in program.skills],
            })
        return rows

    @staticmethod
    def regional_intelligence(db: Session) -> list[dict[str, Any]]:
        learner_rows = db.query(LearnerProfile.district, LearnerProfile.state, LearnerProfile.id).all()
        region = defaultdict(lambda: {"learners": set(), "verified_employed": set(), "jobs": 0, "skills": Counter()})
        for district, state, learner_id in learner_rows:
            key = f"{district}, {state}"
            region[key]["learners"].add(learner_id)

        for row in (
            db.query(EmploymentRecord.learner_id, EmploymentRecord.district, EmploymentRecord.state)
            .filter(EmploymentRecord.verification_status == EmploymentVerificationStatus.EMPLOYER_VERIFIED)
            .all()
        ):
            key = f"{row.district or 'Unknown'}, {row.state or 'Unknown'}"
            region[key]["verified_employed"].add(row.learner_id)

        for posting in db.query(JobPosting).filter(JobPosting.is_active.is_(True)).all():
            key = f"{posting.district}, {posting.state}"
            region[key]["jobs"] += 1
            for skill in posting.skills:
                region[key]["skills"][skill.name] += 1

        output = []
        for key, value in region.items():
            output.append({
                "region": key,
                "learners": len(value["learners"]),
                "verified_employed": len(value["verified_employed"]),
                "employment_rate": round(len(value["verified_employed"]) / len(value["learners"]) * 100, 1) if value["learners"] else 0.0,
                "active_jobs": value["jobs"],
                "top_demand_skills": [name for name, _ in value["skills"].most_common(5)],
            })
        output.sort(key=lambda row: (-row["active_jobs"], row["region"]))
        return output

    @staticmethod
    def deterministic_insight_snapshot(db: Session) -> dict[str, Any]:
        skills = AnalyticsService.skill_supply_demand(db)
        effectiveness = AnalyticsService.training_effectiveness(db)
        overview = AnalyticsService.overview(db)
        high_gaps = [row for row in skills if row["priority"] in {"HIGH", "CRITICAL"}][:5]
        low_employment_programs = sorted(effectiveness, key=lambda row: row["employment_rate"])[:3]
        observations = []
        if overview["employment_rate"] < 60:
            observations.append(f"Verified employment covers {overview['employment_rate']}% of trained learners in the current dataset.")
        if high_gaps:
            observations.append("Several skills have materially higher job-posting demand than demonstrated learner supply.")
        if low_employment_programs:
            observations.append("Some training programs show lower verified-employment conversion than others in the current data.")
        recommendations = []
        for row in high_gaps[:3]:
            recommendations.append(
                f"Investigate curriculum coverage for {row['skill']}: {row['job_demand']} active job requirements versus {row['trained_learners']} learners with demonstrated proficiency."
            )
        recommendations.append("Use employer feedback and verified outcomes as evidence when reviewing curriculum changes; treat these as signals, not proof of causation.")
        return {
            "summary": "The current dataset contains enough evidence to identify priority skill gaps and programs that merit deeper investigation.",
            "observed_facts": observations,
            "priority_skill_gaps": [
                {"skill": row["skill"], "demand": row["job_demand"], "supply": row["trained_learners"], "gap": row["gap"], "priority": row["priority"]}
                for row in high_gaps
            ],
            "program_signals": low_employment_programs,
            "recommended_actions": recommendations,
            "caveat": "Analytics describe observed patterns in the current dataset. They do not establish causal relationships.",
        }
