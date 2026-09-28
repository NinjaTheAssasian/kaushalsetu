from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import csv
import io

from app.api import deps
from app.models import User, UserRole
from app.services.analytics_service import AnalyticsService
from app.services.gemini_service import GeminiService

router = APIRouter()
require_admin = deps.RoleChecker([UserRole.GOVERNMENT_ADMIN])


class AIQuestion(BaseModel):
    question: str = Field(min_length=5, max_length=1000)


def _snapshot(db: Session) -> dict[str, Any]:
    overview = AnalyticsService.overview(db)
    skills = AnalyticsService.skill_supply_demand(db)
    training = AnalyticsService.training_effectiveness(db)
    regions = AnalyticsService.regional_intelligence(db)
    return {
        "overview": overview,
        "top_skill_gaps": skills[:10],
        "training_effectiveness": training,
        "regional_intelligence": regions[:20],
    }


@router.get("/overview")
def overview(
    db: Session = Depends(deps.get_db),
    _: User = Depends(require_admin),
):
    return AnalyticsService.overview(db)


@router.get("/skills/supply-demand")
def skill_supply_demand(
    db: Session = Depends(deps.get_db),
    _: User = Depends(require_admin),
):
    return {"skills": AnalyticsService.skill_supply_demand(db)}


@router.get("/training-effectiveness")
def training_effectiveness(
    db: Session = Depends(deps.get_db),
    _: User = Depends(require_admin),
):
    return {"programs": AnalyticsService.training_effectiveness(db)}


@router.get("/regions")
def regions(
    db: Session = Depends(deps.get_db),
    _: User = Depends(require_admin),
):
    return {"regions": AnalyticsService.regional_intelligence(db)}


@router.get("/insights")
def insights(
    use_ai: bool = True,
    db: Session = Depends(deps.get_db),
    _: User = Depends(require_admin),
):
    deterministic = AnalyticsService.deterministic_insight_snapshot(db)
    if not use_ai:
        return {**deterministic, "ai_status": "deterministic"}
    return GeminiService.generate_insight(deterministic)


@router.post("/ai/ask")
def ask_ai(
    payload: AIQuestion,
    db: Session = Depends(deps.get_db),
    _: User = Depends(require_admin),
):
    return GeminiService.answer_question(payload.question, _snapshot(db))




@router.get("/export.csv")
def export_csv(
    db: Session = Depends(deps.get_db),
    _: User = Depends(require_admin),
):
    """Export an aggregate, non-PII analytics snapshot for reporting/demo use."""
    overview = AnalyticsService.overview(db)
    skills = AnalyticsService.skill_supply_demand(db)
    programs = AnalyticsService.training_effectiveness(db)
    regions = AnalyticsService.regional_intelligence(db)

    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["section", "metric", "value", "detail"])
    for key, value in overview.items():
        writer.writerow(["overview", key, value, ""])
    for row in skills:
        writer.writerow(["skill", row["skill"], row["gap"], f"demand={row['job_demand']}; supply={row['trained_learners']}; priority={row['priority']}"])
    for row in programs:
        writer.writerow(["program", row["program"], row["employment_rate"], f"completion={row['completion_rate']}%; certification={row['certification_rate']}%"])
    for row in regions:
        writer.writerow(["region", row["region"], row["active_jobs"], f"learners={row['learners']}; employed={row['verified_employed']}"])

    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=kaushalsetu-aggregate-analytics.csv"},
    )

@router.get("/snapshot")
def snapshot(
    db: Session = Depends(deps.get_db),
    _: User = Depends(require_admin),
):
    return _snapshot(db)
