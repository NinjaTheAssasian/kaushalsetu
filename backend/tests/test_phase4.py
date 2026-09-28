import uuid
from datetime import date, timedelta

from app.models import Skill, EmploymentVerificationStatus, ProficiencySource


def _register(client, email, role):
    password = "Test123!"
    res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "role": role,
    })
    assert res.status_code == 200, res.text
    login = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": password,
    })
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _profile_payload():
    return {
        "first_name": "Demo",
        "last_name": "Learner",
        "date_of_birth": "2002-01-01",
        "education_level": "Bachelor's",
        "institution": "Demo Institute",
        "district": "Prayagraj",
        "state": "Uttar Pradesh",
        "current_employment_status": "NOT_CURRENTLY_WORKING",
    }


def test_employment_report_and_employer_verification(client, db_session):
    suffix = uuid.uuid4().hex[:10]
    learner_token = _register(client, f"learner-{suffix}@example.com", "TRAINEE")
    employer_token = _register(client, f"employer-{suffix}@example.com", "EMPLOYER")

    profile = client.put(
        "/api/v1/learners/me",
        json=_profile_payload(),
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert profile.status_code == 200, profile.text

    employer_profile = client.put(
        "/api/v1/employers/me",
        json={
            "organization_name": "Acme Demo Technologies",
            "industry": "Information Technology",
            "registration_number": f"REG-{suffix}",
            "district": "Prayagraj",
            "state": "Uttar Pradesh",
            "website": "https://example.com",
        },
        headers={"Authorization": f"Bearer {employer_token}"},
    )
    assert employer_profile.status_code == 200, employer_profile.text

    employment = client.post(
        "/api/v1/learners/me/employment",
        json={
            "role_title": "Junior Security Analyst",
            "reported_employer_name": "Acme Demo Technologies",
            "industry": "Information Technology",
            "employment_type": "FULL_TIME",
            "district": "Prayagraj",
            "state": "Uttar Pradesh",
            "start_date": (date.today() - timedelta(days=20)).isoformat(),
            "salary_band": "20000-30000",
        },
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert employment.status_code == 200, employment.text
    created = employment.json()
    assert created["verification_status"] == "PENDING"
    assert created["verification_code"]

    outcome = client.post(
        "/api/v1/learners/me/outcomes",
        json={
            "milestone_months": 3,
            "employment_status": "EMPLOYED",
            "employer_name": "Acme Demo Technologies",
            "role_title": "Junior Security Analyst",
            "training_relevance_score": 82,
            "using_training_skills": True,
        },
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert outcome.status_code == 200
    assert outcome.json()["verification_status"] == "SELF_REPORTED"

    records = client.get(
        "/api/v1/learners/me/employment",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert records.status_code == 200
    assert len(records.json()) == 1
    assert records.json()[0]["reported_employer_name"] == "Acme Demo Technologies"

    verify = client.post(
        "/api/v1/employment/verify",
        json={"verification_code": created["verification_code"]},
        headers={"Authorization": f"Bearer {employer_token}"},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["status"] == "EMPLOYER_VERIFIED"

    records = client.get(
        "/api/v1/learners/me/employment",
        headers={"Authorization": f"Bearer {learner_token}"},
    ).json()
    assert records[0]["verification_status"] == "EMPLOYER_VERIFIED"

    outcomes = client.get(
        "/api/v1/learners/me/outcomes",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert outcomes.status_code == 200
    assert outcomes.json()[0]["verification_status"] == "EMPLOYER_VERIFIED"
    assert records[0]["employer_name"] == "Acme Demo Technologies"

    employer_records = client.get(
        "/api/v1/employers/me/employments",
        headers={"Authorization": f"Bearer {employer_token}"},
    )
    assert employer_records.status_code == 200
    assert len(employer_records.json()) == 1


def test_employer_skill_feedback_updates_verified_skill(client, db_session):
    suffix = uuid.uuid4().hex[:10]
    learner_token = _register(client, f"learner-feedback-{suffix}@example.com", "TRAINEE")
    employer_token = _register(client, f"employer-feedback-{suffix}@example.com", "EMPLOYER")

    client.put(
        "/api/v1/learners/me",
        json=_profile_payload(),
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    client.put(
        "/api/v1/employers/me",
        json={
            "organization_name": "Feedback Labs",
            "industry": "Cybersecurity",
            "registration_number": f"REG-FB-{suffix}",
            "district": "Prayagraj",
            "state": "Uttar Pradesh",
        },
        headers={"Authorization": f"Bearer {employer_token}"},
    )

    skill = Skill(
        name=f"SIEM-{suffix}",
        normalized_name=f"siem-{suffix}",
        category="Cybersecurity",
        description="Security information and event management",
    )
    db_session.add(skill)
    db_session.commit()
    db_session.refresh(skill)

    created = client.post(
        "/api/v1/learners/me/employment",
        json={
            "role_title": "SOC Analyst",
            "reported_employer_name": "Feedback Labs",
            "industry": "Cybersecurity",
            "employment_type": "FULL_TIME",
            "district": "Prayagraj",
            "state": "Uttar Pradesh",
            "start_date": date.today().isoformat(),
            "salary_band": "25000-35000",
        },
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    code = created.json()["verification_code"]
    employment_id = created.json()["id"]

    verify = client.post(
        "/api/v1/employment/verify",
        json={"verification_code": code},
        headers={"Authorization": f"Bearer {employer_token}"},
    )
    assert verify.status_code == 200

    feedback = client.post(
        f"/api/v1/employment/{employment_id}/feedback",
        json={"skill_id": str(skill.id), "rating": 84, "comments": "Strong practical SIEM usage."},
        headers={"Authorization": f"Bearer {employer_token}"},
    )
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["rating"] == 84
    assert feedback.json()["skill_name"] == skill.name

    rows = client.get(
        f"/api/v1/employment/{employment_id}/feedback",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert rows.status_code == 200
    assert len(rows.json()) == 1

    learner_profile = client.get(
        "/api/v1/learners/me",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    learner_id = uuid.UUID(learner_profile.json()["id"])
    learner_skill = (
        db_session.query(__import__("app.models", fromlist=["LearnerSkill"]).LearnerSkill)
        .filter_by(learner_id=learner_id, skill_id=skill.id)
        .first()
    )
    assert learner_skill is not None
    assert learner_skill.proficiency_score == 84
    assert learner_skill.proficiency_source == ProficiencySource.EMPLOYER
    assert learner_skill.verified is True


def test_employment_privacy_and_permissions(client):
    suffix = uuid.uuid4().hex[:10]
    learner_token = _register(client, f"learner-private-{suffix}@example.com", "TRAINEE")
    other_learner_token = _register(client, f"learner-other-{suffix}@example.com", "TRAINEE")
    employer_token = _register(client, f"employer-private-{suffix}@example.com", "EMPLOYER")

    for token in [learner_token, other_learner_token]:
        res = client.put(
            "/api/v1/learners/me",
            json=_profile_payload(),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200

    client.put(
        "/api/v1/employers/me",
        json={
            "organization_name": "Private Demo Employer",
            "industry": "IT",
            "registration_number": f"REG-{suffix}",
            "district": "Prayagraj",
            "state": "Uttar Pradesh",
        },
        headers={"Authorization": f"Bearer {employer_token}"},
    )

    created = client.post(
        "/api/v1/learners/me/employment",
        json={
            "role_title": "Analyst",
            "reported_employer_name": "Private Demo Employer",
            "employment_type": "FULL_TIME",
            "start_date": date.today().isoformat(),
        },
        headers={"Authorization": f"Bearer {learner_token}"},
    ).json()

    other_list = client.get(
        "/api/v1/learners/me/employment",
        headers={"Authorization": f"Bearer {other_learner_token}"},
    )
    assert other_list.status_code == 200
    assert other_list.json() == []

    employer_feedback = client.post(
        f"/api/v1/employment/{created['id']}/feedback",
        json={"skill_id": str(uuid.uuid4()), "rating": 50},
        headers={"Authorization": f"Bearer {employer_token}"},
    )
    assert employer_feedback.status_code == 403
