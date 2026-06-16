from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


_INITIAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities_state():
    activities.clear()
    activities.update(deepcopy(_INITIAL_ACTIVITIES))


client = TestClient(app)


def activity_path(activity_name: str) -> str:
    return quote(activity_name, safe="")


def test_get_activities_returns_data_and_cache_header():
    # Arrange
    endpoint = "/activities"

    # Act
    response = client.get(endpoint)

    # Assert
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"

    data = response.json()
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_adds_participant():
    # Arrange
    email = "new-student@mergington.edu"
    endpoint = f"/activities/{activity_path('Chess Club')}/signup"

    # Act
    response = client.post(endpoint, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant():
    # Arrange
    existing_email = activities["Chess Club"]["participants"][0]
    endpoint = f"/activities/{activity_path('Chess Club')}/signup"

    # Act
    response = client.post(endpoint, params={"email": existing_email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_signup_rejects_unknown_activity():
    # Arrange
    email = "student@mergington.edu"
    endpoint = f"/activities/{activity_path('Unknown Club')}/signup"

    # Act
    response = client.post(endpoint, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant():
    # Arrange
    email = activities["Chess Club"]["participants"][0]
    endpoint = f"/activities/{activity_path('Chess Club')}/participants"

    # Act
    response = client.delete(endpoint, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in activities["Chess Club"]["participants"]


def test_unregister_rejects_student_not_signed_up():
    # Arrange
    email = "missing@mergington.edu"
    endpoint = f"/activities/{activity_path('Chess Club')}/participants"

    # Act
    response = client.delete(endpoint, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
