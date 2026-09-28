import uuid


def _unique(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"


def setup_certification_flow(client, db_session):
    provider_email = _unique("cert_provider")
    learner_email = _unique("cert_learner")

    client.post(
        "/api/v1/auth/register",
        json={"email": provider_email, "password": "pass", "role": "TRAINING_PROVIDER"},
    )
    provider_token = client.post(
        "/api/v1/auth/login", data={"username": provider_email, "password": "pass"}
    ).json()["access_token"]

    client.post(
        "/api/v1/auth/register",
        json={"email": learner_email, "password": "pass", "role": "TRAINEE"},
    )
    learner_token = client.post(
        "/api/v1/auth/login", data={"username": learner_email, "password": "pass"}
    ).json()["access_token"]

    client.put(
        "/api/v1/learners/me",
        json={
            "first_name": "Cert",
            "last_name": "Learner",
            "date_of_birth": "2001-01-01",
            "education_level": "B.Tech",
            "district": "D1",
            "state": "S1",
            "current_employment_status": "SEEKING_EMPLOYMENT",
        },
        headers={"Authorization": f"Bearer {learner_token}"},
    )

    program = client.post(
        "/api/v1/training-programs/programs",
        json={
            "name": "Cybersecurity Fundamentals",
            "description": "Certification test program",
            "category": "Cybersecurity",
            "duration_hours": 100,
            "start_date": "2026-01-01",
            "capacity": 20,
        },
        headers={"Authorization": f"Bearer {provider_token}"},
    )
    assert program.status_code == 200
    program_id = program.json()["id"]

    enrollment = client.post(
        "/api/v1/enrollments/",
        json={"training_program_id": program_id},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert enrollment.status_code == 200
    enrollment_id = enrollment.json()["id"]
    learner_id = enrollment.json()["learner_id"]

    assessment = client.post(
        f"/api/v1/training-programs/{program_id}/assessments",
        json={
            "name": "Final Assessment",
            "assessment_type": "FINAL",
            "max_score": 100,
            "passing_score": 60,
        },
        headers={"Authorization": f"Bearer {provider_token}"},
    )
    assert assessment.status_code == 200
    assessment_id = assessment.json()["id"]

    from app.models import Skill, LearnerSkill, ProficiencySource
    skill = Skill(name=f"Cloud Security {uuid.uuid4().hex[:6]}", normalized_name=uuid.uuid4().hex, category="Cybersecurity")
    strong_skill = Skill(name=f"Linux {uuid.uuid4().hex[:6]}", normalized_name=uuid.uuid4().hex, category="Cybersecurity")
    db_session.add_all([skill, strong_skill])
    db_session.flush()
    db_session.add(LearnerSkill(learner_id=learner_id, skill_id=strong_skill.id, proficiency_score=90, proficiency_source=ProficiencySource.LEARNER, verified=False))
    db_session.flush()

    return {
        "provider_token": provider_token,
        "learner_token": learner_token,
        "program_id": program_id,
        "enrollment_id": enrollment_id,
        "learner_id": learner_id,
        "assessment_id": assessment_id,
        "skill_id": str(skill.id),
        "strong_skill_id": str(strong_skill.id),
    }


def test_certificate_requires_completion_and_passed_assessments(client, db_session):
    data = setup_certification_flow(client, db_session)

    response = client.post(
        f"/api/v1/enrollments/{data['enrollment_id']}/certificate",
        json={"skill_ids": [data["skill_id"]]},
        headers={"Authorization": f"Bearer {data['provider_token']}"},
    )
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"]


def test_certificate_issue_and_verification(client, db_session):
    data = setup_certification_flow(client, db_session)

    result = client.post(
        f"/api/v1/assessments/{data['assessment_id']}/results",
        json={"learner_id": data["learner_id"], "score": 90, "attempt_number": 1},
        headers={"Authorization": f"Bearer {data['provider_token']}"},
    )
    assert result.status_code == 200
    assert result.json()["passed"] is True

    progress = client.put(
        f"/api/v1/enrollments/{data['enrollment_id']}/progress",
        json={"status": "COMPLETED", "completion_percentage": 100},
        headers={"Authorization": f"Bearer {data['provider_token']}"},
    )
    assert progress.status_code == 200

    certificate = client.post(
        f"/api/v1/enrollments/{data['enrollment_id']}/certificate",
        json={
            "certificate_name": "Cybersecurity Fundamentals Certificate",
            "skill_ids": [data["skill_id"], data["strong_skill_id"]],
        },
        headers={"Authorization": f"Bearer {data['provider_token']}"},
    )
    assert certificate.status_code == 200
    cert_data = certificate.json()
    assert cert_data["status"] == "ISSUED"
    assert cert_data["certificate_number"].startswith("KS-")
    assert cert_data["verification_code"]

    learner_certs = client.get(
        "/api/v1/certificates/me",
        headers={"Authorization": f"Bearer {data['learner_token']}"},
    )
    assert learner_certs.status_code == 200
    assert len(learner_certs.json()) == 1

    verify = client.get(f"/api/v1/certificates/verify/{cert_data['verification_code']}")
    assert verify.status_code == 200
    assert verify.json()["valid"] is True
    assert verify.json()["program_name"] == "Cybersecurity Fundamentals"
    assert verify.json()["skills"]

    from app.models import LearnerSkill
    fresh = db_session.query(LearnerSkill).filter(LearnerSkill.learner_id == data["learner_id"]).all()
    by_skill = {str(row.skill_id): row for row in fresh}
    assert by_skill[data["skill_id"]].proficiency_score == 70
    assert by_skill[data["strong_skill_id"]].proficiency_score == 90

    eligibility = client.get(
        f"/api/v1/enrollments/{data['enrollment_id']}/certificate-eligibility",
        headers={"Authorization": f"Bearer {data['learner_token']}"},
    )
    assert eligibility.status_code == 200
    assert eligibility.json()["eligible"] is True

    revoke = client.post(
        f"/api/v1/certificates/{cert_data['id']}/revoke",
        headers={"Authorization": f"Bearer {data['provider_token']}"},
    )
    assert revoke.status_code == 200
    verify_revoked = client.get(f"/api/v1/certificates/verify/{cert_data['verification_code']}")
    assert verify_revoked.status_code == 200
    assert verify_revoked.json()["valid"] is False
    assert verify_revoked.json()["status"] == "REVOKED"
