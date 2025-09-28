from fastapi.testclient import TestClient
from services.xikizpedia_api.main import app

client = TestClient(app)

def test_login_for_access_token():
    """
    Tests that a user can successfully log in and receive an access token.
    """
    response = client.post("/auth/login", data={"username": "testuser", "password": "password123"})
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

def test_read_leaderboard_unauthenticated():
    """
    Tests that accessing a protected endpoint without a token fails.
    """
    response = client.get("/leaderboard/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_read_leaderboard_authenticated():
    """
    Tests that a user can access a protected endpoint with a valid token.
    """
    # First, log in to get a token
    login_response = client.post("/auth/login", data={"username": "testuser", "password": "password123"})
    token = login_response.json()["access_token"]

    # Now, make the authenticated request
    headers = {"Authorization": f"Bearer {token}"}
    leaderboard_response = client.get("/leaderboard/", headers=headers)
    assert leaderboard_response.status_code == 200
    # The response should be a list (even if it's empty)
    assert isinstance(leaderboard_response.json(), list)