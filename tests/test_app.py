import copy
import pytest

from fastapi.testclient import TestClient

from src.app import app, activities as activities_store


# Keep a snapshot of the original activities so tests run isolated
_ORIGINAL_ACTIVITIES = copy.deepcopy(activities_store)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities database before each test."""
    activities_store.clear()
    activities_store.update(copy.deepcopy(_ORIGINAL_ACTIVITIES))
    yield


def test_get_activities_returns_activities():
    client = TestClient(app)
    resp = client.get("/activities")
    assert resp.status_code == 200
    json_data = resp.json()
    # Expect some known activities from the example seed data
    assert "Chess Club" in json_data
    assert isinstance(json_data["Chess Club"]["participants"], list)


def test_signup_adds_participant_and_prevents_duplicates():
    client = TestClient(app)
    activity = "Chess Club"
    new_email = "teststudent@example.com"

    # Make sure email isn't already present
    assert new_email not in activities_store[activity]["participants"]

    # Sign up should succeed
    resp = client.post(f"/activities/{activity}/signup?email={new_email}")
    assert resp.status_code == 200
    assert new_email in activities_store[activity]["participants"]
    assert "Signed up" in resp.json().get("message", "")

    # Signing up again should be rejected (duplicate)
    resp2 = client.post(f"/activities/{activity}/signup?email={new_email}")
    assert resp2.status_code == 400


def test_unregister_removes_participant_and_errors_when_missing():
    client = TestClient(app)
    activity = "Programming Class"
    test_email = "tempremove@example.com"

    # Ensure the test participant is present (add then remove)
    activities_store[activity]["participants"].append(test_email)
    assert test_email in activities_store[activity]["participants"]

    # Unregister should succeed
    resp = client.delete(f"/activities/{activity}/unregister?email={test_email}")
    assert resp.status_code == 200
    assert test_email not in activities_store[activity]["participants"]

    # Unregistering again should return 404
    resp2 = client.delete(f"/activities/{activity}/unregister?email={test_email}")
    assert resp2.status_code == 404
