# Phase 5: Government Outcome Intelligence + Gemini

Phase 5 adds:

- Employer job postings and skill requirements.
- Training-program-to-skill curriculum mappings.
- Government aggregate analytics: learner funnel, completion, certification, verified employment, 3/6/12 month outcomes, retention, training effectiveness, regional demand, and skill supply vs demand.
- Government-only analytics APIs under `/api/v1/admin/analytics`.
- Employer job-posting APIs under `/api/v1/jobs`.
- Server-side Gemini decision support using `google-genai` structured JSON output.
- Deterministic fallback analytics when Gemini is not configured or temporarily unavailable.
- Government dashboard UI with supply/demand bars, program outcomes, regional intelligence, and an AI copilot.

Gemini API keys are server-side only. No APAAR identifiers are sent to Gemini. The implementation uses the official `google-genai` SDK and structured response schemas.
