"""Local end-to-end smoke checks for the SIH demo deployment.

Requires the FastAPI server to be running on http://localhost:8000.
Uses seeded demo credentials and checks role-specific API access without touching
or printing PII beyond the demo account email addresses supplied here.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import httpx

BASE = "http://localhost:8000/api/v1"


@dataclass(frozen=True)
class DemoAccount:
    label: str
    email: str
    password: str
    expected_role: str


ACCOUNTS = [
    DemoAccount("learner", "learner1@example.com", "learner123", "TRAINEE"),
    DemoAccount("employer", "hr@techcorp.com", "emp123", "EMPLOYER"),
    DemoAccount("provider", "provider@training.com", "provider123", "TRAINING_PROVIDER"),
    DemoAccount("government", "admin@gov.in", "admin123", "GOVERNMENT_ADMIN"),
]


def login(client: httpx.Client, account: DemoAccount) -> str:
    response = client.post(
        f"{BASE}/auth/login",
        data={"username": account.email, "password": account.password},
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    me = client.get(f"{BASE}/auth/me", headers={"Authorization": f"Bearer {token}"})
    me.raise_for_status()
    if me.json().get("role") != account.expected_role:
        raise AssertionError(f"{account.label}: unexpected role")
    return token


def check(name: str, response: httpx.Response, expected: int = 200) -> None:
    if response.status_code != expected:
        raise AssertionError(f"{name}: expected {expected}, got {response.status_code}: {response.text[:200]}")
    print(f"PASS  {name}")


def main() -> int:
    try:
        with httpx.Client(timeout=10.0) as client:
            check("health", client.get(f"{BASE}/health"))

            tokens = {}
            for account in ACCOUNTS:
                tokens[account.label] = login(client, account)
                print(f"PASS  {account.label} login + role")

            headers = {"Authorization": f"Bearer {tokens['learner']}"}
            check("learner enrollments", client.get(f"{BASE}/enrollments/me", headers=headers))
            check("learner employment", client.get(f"{BASE}/learners/me/employment", headers=headers))
            check("learner timeline", client.get(f"{BASE}/learners/me/timeline", headers=headers))

            headers = {"Authorization": f"Bearer {tokens['employer']}"}
            check("employer verified employments", client.get(f"{BASE}/employers/me/employments", headers=headers))
            check("employer blocked from government analytics", client.get(f"{BASE}/admin/analytics/overview", headers=headers), 403)

            headers = {"Authorization": f"Bearer {tokens['provider']}"}
            check("provider programs", client.get(f"{BASE}/training-programs/programs", headers=headers))
            check("provider blocked from government analytics", client.get(f"{BASE}/admin/analytics/overview", headers=headers), 403)

            headers = {"Authorization": f"Bearer {tokens['government']}"}
            check("government overview", client.get(f"{BASE}/admin/analytics/overview", headers=headers))
            check("government skill supply-demand", client.get(f"{BASE}/admin/analytics/skills/supply-demand", headers=headers))
            check("government export", client.get(f"{BASE}/admin/analytics/export.csv", headers=headers))

        print("\nPhase 6 API smoke checks passed.")
        return 0
    except Exception as exc:
        print(f"\nPhase 6 smoke check failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
