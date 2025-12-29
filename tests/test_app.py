"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Basketball": {
            "description": "Team basketball practice and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
        "Soccer": {
            "description": "Competitive soccer team for all skill levels",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 22,
            "participants": ["alex@mergington.edu", "sam@mergington.edu"]
        },
    })


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Basketball" in data
        assert "Soccer" in data

    def test_get_activities_returns_activity_details(self, client):
        """Test that activity details are correctly returned"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2

    def test_get_activities_includes_participants(self, client):
        """Test that participants are included in the response"""
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant(self, client):
        """Test signing up a new participant"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity"""
        client.post(
            "/activities/Basketball/signup?email=newstudent@mergington.edu"
        )
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Basketball"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/NonexistentClub/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_already_registered(self, client):
        """Test signing up when already registered"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_different_activities(self, client):
        """Test signing up for multiple different activities"""
        email = "multistudent@mergington.edu"
        response1 = client.post(f"/activities/Chess%20Club/signup?email={email}")
        response2 = client.post(f"/activities/Basketball/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        assert email in data["Chess Club"]["participants"]
        assert email in data["Basketball"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]

    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/NonexistentClub/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_registered(self, client):
        """Test unregistering when not registered"""
        response = client.delete(
            "/activities/Basketball/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_all_participants(self, client):
        """Test unregistering all participants from an activity"""
        email1 = "michael@mergington.edu"
        email2 = "daniel@mergington.edu"
        
        response1 = client.delete(f"/activities/Chess%20Club/unregister?email={email1}")
        response2 = client.delete(f"/activities/Chess%20Club/unregister?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        response = client.get("/activities")
        data = response.json()
        assert len(data["Chess Club"]["participants"]) == 0


class TestIntegration:
    """Integration tests combining multiple endpoints"""

    def test_signup_then_unregister(self, client):
        """Test signing up and then unregistering"""
        email = "student@mergington.edu"
        
        # Sign up
        response1 = client.post(f"/activities/Soccer/signup?email={email}")
        assert response1.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()["Soccer"]["participants"]
        
        # Unregister
        response2 = client.delete(f"/activities/Soccer/unregister?email={email}")
        assert response2.status_code == 200
        
        # Verify unregister
        response = client.get("/activities")
        assert email not in response.json()["Soccer"]["participants"]

    def test_participant_count_updates(self, client):
        """Test that participant count updates correctly"""
        email = "student@mergington.edu"
        
        response = client.get("/activities")
        initial_count = len(response.json()["Basketball"]["participants"])
        
        client.post(f"/activities/Basketball/signup?email={email}")
        response = client.get("/activities")
        after_signup = len(response.json()["Basketball"]["participants"])
        assert after_signup == initial_count + 1
        
        client.delete(f"/activities/Basketball/unregister?email={email}")
        response = client.get("/activities")
        after_unregister = len(response.json()["Basketball"]["participants"])
        assert after_unregister == initial_count
