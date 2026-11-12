from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


ORIGINAL_ACTIVITIES = deepcopy(activities)
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))
    yield
    activities.clear()
    activities.update(deepcopy(ORIGINAL_ACTIVITIES))


def test_get_activities_returns_activity_list():
    # Arrange
    expected_activities = deepcopy(ORIGINAL_ACTIVITIES)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_student_to_activity():
    # Arrange
    activity_name = "Basketball Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_for_unknown_activity_returns_not_found():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_full_activity_refuses_new_student():
    # Arrange
    activity_name = "Basketball Club"
    activity = activities[activity_name]
    activity["participants"] = [
        f"participant-{index}@mergington.edu"
        for index in range(activity["max_participants"])
    ]
    participants_before_signup = activity["participants"].copy()
    email = "new-student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Activity is full"}
    assert activity["participants"] == participants_before_signup
    assert email not in activity["participants"]


def test_last_available_place_is_accepted_then_activity_is_full():
    # Arrange
    activity_name = "Basketball Club"
    activity = activities[activity_name]
    activity["participants"] = [
        f"participant-{index}@mergington.edu"
        for index in range(activity["max_participants"] - 1)
    ]
    last_student = "last-student@mergington.edu"
    next_student = "next-student@mergington.edu"

    # Act
    last_signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": last_student},
    )
    next_signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": next_student},
    )

    # Assert
    assert last_signup_response.status_code == 200
    assert last_student in activity["participants"]
    assert next_signup_response.status_code == 400
    assert next_signup_response.json() == {"detail": "Activity is full"}
    assert len(activity["participants"]) == activity["max_participants"]
    assert next_student not in activity["participants"]


def test_duplicate_signup_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    email = ORIGINAL_ACTIVITIES[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}
