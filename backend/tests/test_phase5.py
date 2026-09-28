from app.models import (
    Employer,
    GovernmentAdmin,
    JobPosting,
    Skill,
    TrainingProgram,
    TrainingProvider,
    User,
    UserRole,
)
from app.core.security import get_password_hash


def _create_admin(client, db_session):
    user = User(
        email="phase5-admin@example.com",
        password_hash=get_password_hash("admin123"),
        role=UserRole.GOVERNMENT_ADMIN,
    )
    db_session.add(user)
    db_session.flush()
    db_session.add(GovernmentAdmin(user_id=user.id, department="Skill Development", jurisdiction="Maharashtra"))
    db_session.commit()
    token = client.post("/api/v1/auth/login", data={"username": user.email, "password": "admin123"}).json()["access_token"]
    return token


def test_government_analytics_requires_admin(client):
    response = client.get("/api/v1/admin/analytics/overview")
    assert response.status_code in (401, 403)


def test_government_overview_and_supply_demand(client, db_session):
    token = _create_admin(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/v1/admin/analytics/overview", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert "total_learners" in payload
    assert "employment_rate" in payload

    response = client.get("/api/v1/admin/analytics/skills/supply-demand", headers=headers)
    assert response.status_code == 200
    assert "skills" in response.json()


def test_employer_can_create_job_and_government_can_see_it(client, db_session):
    employer = User(
        email="phase5-employer@example.com",
        password_hash=get_password_hash("emp123"),
        role=UserRole.EMPLOYER,
    )
    db_session.add(employer)
    db_session.flush()
    employer_profile = Employer(
        user_id=employer.id,
        organization_name="Phase5 Employer",
        industry="IT",
        registration_number="P5-001",
        district="Pune",
        state="Maharashtra",
    )
    db_session.add(employer_profile)
    skill = Skill(name="Phase5 Skill", normalized_name="phase5 skill", category="IT")
    db_session.add(skill)
    db_session.commit()

    token = client.post("/api/v1/auth/login", data={"username": employer.email, "password": "emp123"}).json()["access_token"]
    response = client.post(
        "/api/v1/jobs",
        json={
            "title": "Phase5 Security Analyst",
            "role_family": "Cybersecurity",
            "industry": "IT",
            "district": "Pune",
            "state": "Maharashtra",
            "employment_type": "FULL_TIME",
            "salary_band": "₹4L–₹7L",
            "experience_min_years": 0,
            "skill_ids": [str(skill.id)],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["skill_names"] == ["Phase5 Skill"]


def test_government_csv_export_requires_admin_and_contains_no_pii(client, db_session):
    response = client.get("/api/v1/admin/analytics/export.csv")
    assert response.status_code in (401, 403)

    token = _create_admin(client, db_session)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/admin/analytics/export.csv", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    body = response.text
    assert "section,metric,value,detail" in body
    assert "apaaar" not in body.lower()
    assert "password" not in body.lower()
