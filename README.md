# KaushalSetu - Phase 1

Longitudinal Skill & Employment Outcome Intelligence Platform

## Phase 1 goals
- Monorepo scaffold
- Next.js + TypeScript frontend
- FastAPI backend
- PostgreSQL via Docker Compose
- Environment variable templates
- Health-check endpoint
- Clean service/module boundaries for later phases

## Stack
- Frontend: Next.js + TypeScript
- Backend: FastAPI + Python
- Database: PostgreSQL
- Future AI: Gemini API via server-side service layer

## Run

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Database
```bash
docker compose up -d db
```

Backend health: http://localhost:8000/api/v1/health
Frontend: http://localhost:3000

## Environment
Copy `.env.example` to `.env` in the relevant directory.
Never commit real Gemini/API secrets.

## Phase 2
- Integrated Identity, Authentication, and Role-Based Access.
- Implemented Core Database Models (User, LearnerProfile, TrainingProvider, Employer, GovernmentAdmin, Skill, LearnerSkill, CareerEvent, TrainingProgram, TrainingEnrollment).
- Configured secure JWT authentication (Argon2 for passwords).
- Added Mock APAAR verification endpoint (securely hashing ID without exposing).
- Database migrations handled via **Alembic**.
- Role-based authorization enforced via FastAPI dependencies.
- Frontend includes auth foundations (/login, /register, /profile).

### Getting Started (Backend)
1. Install dependencies: pip install -r requirements.txt
2. Start PostgreSQL: docker-compose up -d
3. Run DB Migrations: lembic upgrade head
4. Seed the DB: python scripts/seed_db.py (Default accounts like admin@gov.in / admin123, learner1@example.com / learner123)
5. Run the API: uvicorn app.main:app --reload
6. Run tests: $env:PYTHONPATH='.'; pytest tests/ (Powershell)

### Endpoints Added
- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/auth/me
- POST /api/v1/apaar/verify
- GET /api/v1/apaar/status
- Plus other REST endpoints for learner profiles, training programs, and skills.


## Phase 3A (Training + Attendance + Assessment)
- Introduced \AttendanceRecord\ to log daily attendance for active enrollments.
- Introduced \Assessment\ and \AssessmentResult\ models to capture evaluation workflows.
- Training Providers can record attendance and assessment results for learners enrolled in their programs.
- Trainees can view their own enrollment progress and final scores.
- Implemented robust RBAC: Learners cannot view peers' results, and Providers cannot evaluate programs outside their jurisdiction.

### Getting Started (Backend)
1. Run migrations: \lembic upgrade head\
2. Run tests: \$env:PYTHONPATH='.'; pytest tests/\
3. Seed DB with assessments and attendance: \python scripts/seed_db.py\

### New Endpoints
- \POST /api/v1/enrollments/{enrollment_id}/attendance\
- \GET /api/v1/enrollments/{enrollment_id}/attendance\
- \POST /api/v1/training-programs/{program_id}/assessments\
- \GET /api/v1/training-programs/{program_id}/assessments\
- \POST /api/v1/assessments/{assessment_id}/results\
- \GET /api/v1/learners/me/assessments\


## Phase 3B/3C (Certification + Longitudinal Outcomes)
- Added certificate lifecycle with eligibility checks based on training completion and passed assessments.
- Added certificate verification using a non-PII verification code; public verification never exposes APAAR ID.
- Certificates can map to skills. Certificate-derived skills are written to the learner skill profile with `CERTIFICATION` as the source and do not overwrite a stronger existing proficiency signal.
- Certificate issuance automatically creates a `CERTIFICATION` career event.
- Added provider-controlled enrollment progress updates so a training provider can mark a learner's training complete.
- Added learner 3/6/12-month outcome check-ins covering employment status, role, income band, training relevance, skill use, and skill-gap notes. These are explicitly self-reported until future verification flows are added.
- Added a combined learner career timeline from enrollment, training completion, assessment results, certifications, career events, and outcome check-ins.
- Added learner certificate and longitudinal outcome sections to the profile UI plus a public `/verify` certificate verification page.
- Added provider workflow UI for completion and certificate issuance.

### Phase 3 migration
```bash
alembic upgrade head
```

### Phase 3 seed helper
The existing development seed remains available. To add Phase 3 certificates and outcome samples to an existing seeded database, run:
```bash
python scripts/seed_phase3.py
```

### Phase 3 endpoints
- `PUT /api/v1/enrollments/{enrollment_id}/progress`
- `POST /api/v1/enrollments/{enrollment_id}/certificate`
- `GET /api/v1/enrollments/{enrollment_id}/certificate-eligibility`
- `GET /api/v1/certificates/me`
- `GET /api/v1/certificates/{certificate_id}`
- `GET /api/v1/certificates/eligibility/{enrollment_id}`
- `GET /api/v1/certificates/verify/{verification_code}`
- `GET /api/v1/training-programs/{program_id}/enrollments`
- `POST /api/v1/learners/me/outcomes`
- `GET /api/v1/learners/me/outcomes`
- `GET /api/v1/learners/me/timeline`

### Phase 3 testing
```bash
$env:PYTHONPATH='.'
pytest tests/ -v
```


## Phase 4: Employer Integration

Phase 4 adds learner employment reporting, one-time employer verification, employer profiles, and employer skill feedback. See `docs/phase-4-architecture.md`.

Run the demo seed after the existing seed/Phase 3 data is present:

```powershell
.\.venv\Scripts\python.exe scripts\seed_phase4.py
```


## Phase 6
- Final integration and SIH demo polish.
- Role-aware demo navigation.
- Government aggregate CSV export and print-ready executive brief.
- Learner employment verification code copy workflow.
- See `PHASE6_COMPLETE.md`.

## Phase 6: Final Integration + Demo Polish

The final SIH demo path is role-aware and explicit:

1. Learner signs in, verifies the demo APAAR identity, and reports employment.
2. Learner copies the one-time employment verification code.
3. Employer signs in and verifies the employment using that code.
4. Employer adds skill feedback.
5. Learner sees verified evidence and longitudinal outcomes.
6. Government signs in to review aggregate intelligence and Gemini decision support.

Government administrators can export the aggregate dashboard as CSV from:
`GET /api/v1/admin/analytics/export.csv`

Run the local API smoke checks after starting FastAPI and seeding demo data:
```powershell
.\.venv\Scripts\python.exe scripts\smoke_phase6.py
```
