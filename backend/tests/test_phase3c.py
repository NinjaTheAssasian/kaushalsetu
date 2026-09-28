import uuid


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"


def _create_learner(client):
    email = _unique("outcome_learner")
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "pass", "role": "TRAINEE"},
    )
    assert reg.status_code == 200
    token = client.post(
        "/api/v1/auth/login", data={"username": email, "password": "pass"}
    ).json()["access_token"]
    client.put(
        "/api/v1/learners/me",
        json={
            "first_name": "Outcome",
            "last_name": "Learner",
            "date_of_birth": "2002-02-02",
            "education_level": "B.Tech",
            "district": "Prayagraj",
            "state": "Uttar Pradesh",
            "current_employment_status": "SEEKING_EMPLOYMENT",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    return token


def test_outcome_checkins_and_timeline(client):
    token = _create_learner(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/learners/me/outcomes",
        json={
            "milestone_months": 3,
            "check_in_date": "2026-04-01",
            "employment_status": "EMPLOYED",
            "employer_name": "DemoTech",
            "role_title": "Junior Analyst",
            "industry": "IT",
            "district": "Prayagraj",
            "state": "Uttar Pradesh",
            "income_band": "20000-30000",
            "same_employer": True,
            "training_relevance_score": 85,
            "using_training_skills": True,
            "skill_gap_notes": "Needs more cloud exposure",
        },
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["verification_status"] == "SELF_REPORTED"

    # Same milestone behaves as an idempotent update rather than creating duplicates.
    update = client.post(
        "/api/v1/learners/me/outcomes",
        json={
            "milestone_months": 3,
            "employment_status": "EMPLOYED",
            "role_title": "Analyst",
            "training_relevance_score": 90,
        },
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["role_title"] == "Analyst"

    bad = client.post(
        "/api/v1/learners/me/outcomes",
        json={
            "milestone_months": 9,
            "employment_status": "EMPLOYED",
        },
        headers=headers,
    )
    assert bad.status_code == 400

    outcomes = client.get("/api/v1/learners/me/outcomes", headers=headers)
    assert outcomes.status_code == 200
    assert len(outcomes.json()) == 1

    timeline = client.get("/api/v1/learners/me/timeline", headers=headers)
    assert timeline.status_code == 200
    assert any(item["event_type"] == "OUTCOME_CHECK_IN" for item in timeline.json())
