from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import settings


class PrioritySkillGap(BaseModel):
    skill: str
    demand: int = Field(ge=0)
    supply: int = Field(ge=0)
    gap: int = Field(ge=0)
    priority: str
    rationale: str


class GeminiInsight(BaseModel):
    summary: str
    observed_facts: list[str]
    priority_skill_gaps: list[PrioritySkillGap]
    recommended_actions: list[str]
    caveat: str


class GeminiAnswer(BaseModel):
    answer: str
    observed_facts: list[str]
    possible_contributing_factors: list[str]
    recommended_investigation: list[str]
    caveat: str


class GeminiService:
    @staticmethod
    def _client():
        if not settings.gemini_api_key:
            return None
        try:
            from google import genai
        except ImportError:
            return None
        return genai.Client(api_key=settings.gemini_api_key)

    @staticmethod
    def generate_insight(snapshot: dict[str, Any]) -> dict[str, Any]:
        client = GeminiService._client()
        if client is None:
            return {**snapshot, "ai_status": "not_configured"}

        from google.genai import types

        prompt = f"""
You are an evidence-focused government skilling analytics assistant.
Analyze the supplied KaushalSetu aggregate data.
Do not invent facts, do not expose personal data, and do not imply causation from correlation.
Use phrases like 'observed pattern', 'possible contributing factor', and 'recommended investigation'.
Return concise recommendations that a government training program manager could act on.

DATA:
{json.dumps(snapshot, default=str)}
"""
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiInsight,
                ),
            )
            parsed = GeminiInsight.model_validate_json(response.text)
            return {**parsed.model_dump(), "ai_status": "gemini"}
        except Exception as exc:
            return {
                **snapshot,
                "ai_status": "fallback",
                "ai_error": str(exc)[:300],
            }

    @staticmethod
    def answer_question(question: str, dashboard_context: dict[str, Any]) -> dict[str, Any]:
        client = GeminiService._client()
        if client is None:
            return {
                "answer": "Gemini is not configured. Review the observed dashboard metrics and skill gaps shown on this page.",
                "observed_facts": dashboard_context.get("observed_facts", []),
                "possible_contributing_factors": ["Configure GEMINI_API_KEY to enable narrative analysis."],
                "recommended_investigation": ["Compare course coverage, employer feedback, and verified employment outcomes."],
                "caveat": "This fallback is deterministic and does not use an AI model.",
                "ai_status": "not_configured",
            }

        from google.genai import types

        prompt = f"""
You are KaushalSetu's government analytics copilot.
Answer the user's question using ONLY the aggregate context supplied below.
Separate observed facts from possible explanations. Never claim causation without evidence.
Do not mention or infer individual identities.

USER QUESTION:
{question}

AGGREGATE CONTEXT:
{json.dumps(dashboard_context, default=str)}
"""
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiAnswer,
                ),
            )
            parsed = GeminiAnswer.model_validate_json(response.text)
            return {**parsed.model_dump(), "ai_status": "gemini"}
        except Exception as exc:
            return {
                "answer": "The AI service could not complete this request. The deterministic dashboard remains available.",
                "observed_facts": dashboard_context.get("observed_facts", []),
                "possible_contributing_factors": [],
                "recommended_investigation": ["Retry after confirming the Gemini API key and model configuration."],
                "caveat": "AI output was unavailable for this request.",
                "ai_status": "error",
                "ai_error": str(exc)[:300],
            }
