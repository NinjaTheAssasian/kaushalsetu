import pytest


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_user_registration_and_login(client):
    # Register
    register_data = {
        "email": "test_iso@example.com",
        "role": "TRAINEE",
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/register", json=register_data)
    assert response.status_code == 200

    # Login
    login_data = {
        "username": "test_iso@example.com",
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()

    token = response.json()["access_token"]

    # Test protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test_iso@example.com"


def test_role_authorization(client):
    # Register and login as trainee
    client.post("/api/v1/auth/register", json={
        "email": "trainee_role@example.com", "role": "TRAINEE", "password": "testpassword"
    })
    response = client.post("/api/v1/auth/login", data={
        "username": "trainee_role@example.com", "password": "testpassword"
    })
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Trainee tries to access training provider endpoint
    program_data = {
        "name": "Test Program",
        "description": "Test",
        "category": "Test",
        "duration_hours": 10,
        "start_date": "2023-01-01",
        "capacity": 10,
        "is_active": True
    }
    response = client.post("/api/v1/training-programs/programs", json=program_data, headers=headers)
    assert response.status_code == 403  # Forbidden for TRAINEE


def test_apaar_mock(client):
    # Register and login with unique email
    import uuid
    email = f"apaar_{uuid.uuid4().hex[:8]}@test.com"
    client.post("/api/v1/auth/register", json={
        "email": email, "role": "TRAINEE", "password": "testpassword"
    })
    token = client.post("/api/v1/auth/login", data={
        "username": email, "password": "testpassword"
    }).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Use a unique 12-digit APAAR ID to avoid unique constraint collision with seed data
    unique_apaar = str(uuid.uuid4().int)[:12]
    apaar_data = {"apaar_id": unique_apaar}
    response = client.post("/api/v1/apaar/verify", json=apaar_data, headers=headers)
    assert response.status_code == 200
    assert "masked_apaar_id" in response.json()
    assert response.json()["masked_apaar_id"] == f"********{unique_apaar[-4:]}"
    assert "apaar_id" not in response.json()  # Raw ID not exposed

    # Status
    response = client.get("/api/v1/apaar/status", headers=headers)
    assert response.status_code == 200
    assert response.json()["verification_status"] == "VERIFIED"
