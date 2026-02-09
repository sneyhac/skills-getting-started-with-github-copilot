"""Tests for the Mergington High School Activities API"""

import pytest


class TestActivities:
    """Tests for /activities endpoint"""

    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Tennis Club" in data
        assert "Basketball Team" in data


class TestSignup:
    """Tests for signup endpoint"""

    def test_signup_for_activity(self, client):
        """Test signing up for an available activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "test@mergington.edu" in data["message"]

    def test_signup_already_registered(self, client):
        """Test signing up with an email already registered for the activity"""
        # michael@mergington.edu is already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_activity_not_found(self, client):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/Non Existent Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_signup_activity_full(self, client):
        """Test signing up for a full activity"""
        # First, get the activities to see which are full
        activities_response = client.get("/activities")
        activities = activities_response.json()
        
        # Find an activity that's full
        full_activity = None
        for activity_name, activity_data in activities.items():
            if len(activity_data["participants"]) >= activity_data["max_participants"]:
                full_activity = activity_name
                break
        
        # If no full activity exists, skip this test
        if full_activity is None:
            pytest.skip("No full activity available for testing")
        
        response = client.post(
            f"/activities/{full_activity}/signup?email=newuser@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "full" in data["detail"].lower()


class TestUnregister:
    """Tests for unregister endpoint"""

    def test_unregister_from_activity(self, client):
        """Test unregistering from an activity"""
        # First sign up
        signup_response = client.post(
            "/activities/Tennis Club/signup?email=testuser@mergington.edu"
        )
        assert signup_response.status_code == 200
        
        # Then unregister
        response = client.delete(
            "/activities/Tennis Club/unregister?email=testuser@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "testuser@mergington.edu" in data["message"]

    def test_unregister_not_registered(self, client):
        """Test unregistering when not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_activity_not_found(self, client):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/Non Existent Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestParticipantFlow:
    """Integration tests for signup and unregister flow"""

    def test_full_signup_unregister_flow(self, client):
        """Test the complete flow of signing up and then unregistering"""
        email = "integration@mergington.edu"
        activity = "Art Studio"
        
        # Check initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity]["participants"])
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify participant was added
        check_response = client.get("/activities")
        mid_count = len(check_response.json()[activity]["participants"])
        assert mid_count == initial_count + 1
        assert email in check_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify participant was removed
        final_response = client.get("/activities")
        final_count = len(final_response.json()[activity]["participants"])
        assert final_count == initial_count
        assert email not in final_response.json()[activity]["participants"]
