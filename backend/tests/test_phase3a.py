import pytest
import uuid


def _unique(prefix: str) -> str:
    """Generate a unique email so tests never collide with seed data or prior runs."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"


def setup_users(client):
    """Create isolated test users, program, and enrollment within the current transaction."""
    email_prov = _unique("prov")
    email_trn = _unique("trn")
    email_emp = _unique("emp")

    # Create Provider
    client.post("/api/v1/auth/register", json={"email": email_prov, "password": "pass", "role": "TRAINING_PROVIDER"})
    token_prov = client.post("/api/v1/auth/login", data={"username": email_prov, "password": "pass"}).json()["access_token"]

    # Create Trainee
    client.post("/api/v1/auth/register", json={"email": email_trn, "password": "pass", "role": "TRAINEE"})
    token_trn = client.post("/api/v1/auth/login", data={"username": email_trn, "password": "pass"}).json()["access_token"]

    # Create Employer
    client.post("/api/v1/auth/register", json={"email": email_emp, "password": "pass", "role": "EMPLOYER"})
    token_emp = client.post("/api/v1/auth/login", data={"username": email_emp, "password": "pass"}).json()["access_token"]

    # Provider creates a program
    prog_res = client.post("/api/v1/training-programs/programs", json={
        "name": "Phase 3A Program",
        "description": "Test",
        "category": "Test",
        "duration_hours": 10,
        "start_date": "2024-01-01",
        "capacity": 10
    }, headers={"Authorization": f"Bearer {token_prov}"})
    program_id = prog_res.json()["id"]

    # Trainee creates profile and enrolls
    client.put("/api/v1/learners/me", json={
        "first_name": "Test", "last_name": "Trainee", "date_of_birth": "2000-01-01",
        "education_level": "High School", "district": "D1", "state": "S1",
        "current_employment_status": "EMPLOYED"
    }, headers={"Authorization": f"Bearer {token_trn}"})

    enr_res = client.post("/api/v1/enrollments/", json={"training_program_id": program_id},
                          headers={"Authorization": f"Bearer {token_trn}"})
    enrollment_id = enr_res.json()["id"]
    learner_id = enr_res.json()["learner_id"]

    return {
        "prov": token_prov, "trn": token_trn, "emp": token_emp,
        "program_id": program_id, "enrollment_id": enrollment_id, "learner_id": learner_id
    }


def test_phase3a_workflows(client):
    data = setup_users(client)
    token_prov = data["prov"]
    token_trn = data["trn"]
    token_emp = data["emp"]

    # 1. training provider creates assessment for its own program
    ass_res = client.post(f"/api/v1/training-programs/{data['program_id']}/assessments", json={
        "name": "Midterm",
        "assessment_type": "QUIZ",
        "max_score": 100,
        "passing_score": 50
    }, headers={"Authorization": f"Bearer {token_prov}"})
    assert ass_res.status_code == 200
    assessment_id = ass_res.json()["id"]

    # 2. Employer cannot create assessment (unauthorized employer access)
    ass_emp_res = client.post(f"/api/v1/training-programs/{data['program_id']}/assessments", json={
        "name": "Midterm 2", "assessment_type": "QUIZ", "max_score": 100, "passing_score": 50
    }, headers={"Authorization": f"Bearer {token_emp}"})
    assert ass_emp_res.status_code == 403

    # 3. Second provider cannot create assessment for first provider's program
    email_prov2 = _unique("prov2")
    client.post("/api/v1/auth/register", json={"email": email_prov2, "password": "pass", "role": "TRAINING_PROVIDER"})
    token_prov2 = client.post("/api/v1/auth/login", data={"username": email_prov2, "password": "pass"}).json()["access_token"]

    ass_prov2_res = client.post(f"/api/v1/training-programs/{data['program_id']}/assessments", json={
        "name": "Midterm 2", "assessment_type": "QUIZ", "max_score": 100, "passing_score": 50
    }, headers={"Authorization": f"Bearer {token_prov2}"})
    assert ass_prov2_res.status_code == 403

    # 5. attendance can be recorded
    att_res = client.post(f"/api/v1/enrollments/{data['enrollment_id']}/attendance", json={
        "attendance_date": "2024-01-02",
        "status": "PRESENT"
    }, headers={"Authorization": f"Bearer {token_prov}"})
    assert att_res.status_code == 200

    # 6. duplicate attendance date is rejected
    att_res_dup = client.post(f"/api/v1/enrollments/{data['enrollment_id']}/attendance", json={
        "attendance_date": "2024-01-02",
        "status": "PRESENT"
    }, headers={"Authorization": f"Bearer {token_prov}"})
    assert att_res_dup.status_code == 400

    # 7 & 8. assessment score & passing status calculates correctly
    res_res = client.post(f"/api/v1/assessments/{assessment_id}/results", json={
        "learner_id": data["learner_id"],
        "score": 75,
        "attempt_number": 1
    }, headers={"Authorization": f"Bearer {token_prov}"})
    assert res_res.status_code == 200
    res_data = res_res.json()
    assert res_data["percentage"] == 75.0
    assert res_data["passed"] == True

    # 3. learner can view own assessment result
    my_res = client.get("/api/v1/learners/me/assessments", headers={"Authorization": f"Bearer {token_trn}"})
    assert my_res.status_code == 200
    assert len(my_res.json()) == 1
    assert my_res.json()[0]["id"] == res_data["id"]

    # 4. learner cannot view another learner's result
    email_trn2 = _unique("trn2")
    client.post("/api/v1/auth/register", json={"email": email_trn2, "password": "pass", "role": "TRAINEE"})
    token_trn2 = client.post("/api/v1/auth/login", data={"username": email_trn2, "password": "pass"}).json()["access_token"]
    my_res2 = client.get("/api/v1/learners/me/assessments", headers={"Authorization": f"Bearer {token_trn2}"})
    assert my_res2.status_code == 200
    assert len(my_res2.json()) == 0

    # 10. health endpoint still works
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200
    assert health_res.json()["database"] == "ok"
