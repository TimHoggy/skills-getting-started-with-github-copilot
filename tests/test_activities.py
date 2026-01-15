import pytest
from fastapi.testclient import TestClient


def test_get_activities(client: TestClient):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0

    # Check that each activity has the expected structure
    for activity_name, activity_data in data.items():
        assert "description" in activity_data
        assert "schedule" in activity_data
        assert "max_participants" in activity_data
        assert "participants" in activity_data
        assert isinstance(activity_data["participants"], list)


def test_signup_for_activity(client: TestClient):
    """Test signing up for an activity"""
    # First, get the activities to find one to sign up for
    response = client.get("/activities")
    activities = response.json()

    # Find an activity that has space
    activity_name = None
    for name, data in activities.items():
        if len(data["participants"]) < data["max_participants"]:
            activity_name = name
            break

    assert activity_name is not None, "No activity with available spots found"

    # Sign up a new student
    email = "test.student@mergington.edu"
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]

    # Verify the student was added
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate_participant(client: TestClient):
    """Test signing up the same student twice for the same activity"""
    # First, get the activities
    response = client.get("/activities")
    activities = response.json()

    # Find an activity with space
    activity_name = None
    for name, data in activities.items():
        if len(data["participants"]) < data["max_participants"]:
            activity_name = name
            break

    assert activity_name is not None

    # Sign up a student
    email = "duplicate.test@mergington.edu"
    client.post(f"/activities/{activity_name}/signup", params={"email": email})

    # Try to sign up again
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]


def test_signup_nonexistent_activity(client: TestClient):
    """Test signing up for a non-existent activity"""
    response = client.post(
        "/activities/NonExistentActivity/signup",
        params={"email": "test@mergington.edu"}
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


def test_unregister_from_activity(client: TestClient):
    """Test unregistering from an activity"""
    # First, sign up a student
    response = client.get("/activities")
    activities = response.json()

    # Find an activity with participants
    activity_name = None
    for name, data in activities.items():
        if len(data["participants"]) > 0:
            activity_name = name
            break

    if activity_name is None:
        # If no activity has participants, sign someone up first
        activity_name = list(activities.keys())[0]
        email = "unregister.test@mergington.edu"
        client.post(f"/activities/{activity_name}/signup", params={"email": email})
    else:
        email = activities[activity_name]["participants"][0]

    # Unregister the student
    response = client.post(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]

    # Verify the student was removed
    response = client.get("/activities")
    activities = response.json()
    assert email not in activities[activity_name]["participants"]


def test_unregister_not_signed_up(client: TestClient):
    """Test unregistering a student who is not signed up"""
    response = client.get("/activities")
    activities = response.json()
    activity_name = list(activities.keys())[0]

    email = "not.signed.up@mergington.edu"
    response = client.post(
        f"/activities/{activity_name}/unregister",
        params={"email": email}
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not signed up" in data["detail"]


def test_unregister_nonexistent_activity(client: TestClient):
    """Test unregistering from a non-existent activity"""
    response = client.post(
        "/activities/NonExistentActivity/unregister",
        params={"email": "test@mergington.edu"}
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"]


def test_root_redirect(client: TestClient):
    """Test that root path redirects to static index"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert "/static/index.html" in response.headers["location"]