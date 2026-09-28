# Phase 4: Employer Integration

Phase 4 closes the gap between learner self-reported employment and employer-verified outcomes.

## Flow

```text
Learner reports employment
        |
        v
One-time verification code
        |
        v
Employer verifies employment
        |
        v
Employer skill feedback
        |
        v
Learner skill evidence + career event
```

## Data model

### EmploymentRecord

Tracks the employment relationship independently from the learner's profile. Raw verification codes are never stored. A high-entropy code is generated for the learner and only its HMAC-SHA256 digest is persisted.

Key fields:

- learner
- employer (set after verification)
- reported employer name
- role
- industry
- employment type
- location
- start/end dates
- salary band
- active/ended status
- verification status
- verified timestamp

### EmployerSkillFeedback

Employer observations are stored per employment record and skill. A 0-100 rating and optional comments become evidence for the learner's skill profile. An employer feedback score can raise an existing learner skill score, but it never lowers a stronger existing score.

## Security and privacy

- Learners control when a verification code is shared.
- Verification uses a high-entropy one-time code; the database stores only its HMAC digest.
- Raw APAAR is not used in employment APIs.
- Employers can only access employment records they have verified.
- Government admins have read access to individual records for the prototype, while broader analytics belongs to Phase 5.
- Employer feedback requires an employer-verified employment relationship.

## API surface

### Learner

- `POST /api/v1/learners/me/employment`
- `GET /api/v1/learners/me/employment`
- `PUT /api/v1/learners/me/employment/{employment_id}`
- `POST /api/v1/learners/me/employment/{employment_id}/end`
- `POST /api/v1/learners/me/employment/{employment_id}/verification-code`

### Employer

- `GET /api/v1/employers/me`
- `PUT /api/v1/employers/me`
- `POST /api/v1/employment/verify`
- `GET /api/v1/employers/me/employments`
- `POST /api/v1/employment/{employment_id}/feedback`
- `GET /api/v1/employment/{employment_id}/feedback`

### Shared

- `GET /api/v1/employment/{employment_id}`

## Why this matters for the SIH problem

Phase 4 introduces the first independent employer-side evidence layer. The system can now distinguish:

- self-reported employment
- employer-verified employment
- employer-observed skill strength

That evidence will feed Phase 5 outcome analytics and the Gemini skill-gap engine.
