# Phase 1 Architecture

```text
                    Web / Mobile Clients
                           |
                           v
                    Next.js Frontend
                           |
                     REST / JSON
                           |
                           v
                    FastAPI Backend
                  /       |        \
                 /        |         \
          PostgreSQL   AI Service   Auth/RBAC
                            |
                         Gemini API
```

## Planned module boundaries

- Identity: APAAR identity abstraction, consent, masking
- Learners: learner profile and career timeline
- Training: programs, enrollments, assessments, certifications
- Employers: job requirements, employment verification, skill feedback
- Skills: taxonomy, normalized skills, learner proficiency
- Analytics: outcomes, retention, supply vs demand
- AI: server-side Gemini orchestration with structured outputs and fallbacks
- Audit: access logging and sensitive-data events
