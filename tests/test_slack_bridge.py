import os

# Set dummy environment variables BEFORE importing the app
# This prevents the app from crashing on import during test collection
os.environ["SLACK_BOT_TOKEN"] = "xoxb-test"
os.environ["SLACK_SIGNING_SECRET"] = "test-secret"
os.environ["UCAPI_SERVICE_KEY"] = "test-ucapi-key"

import pytest
from unittest.mock import patch, MagicMock
from services.slack import app as slack_app

@pytest.mark.asyncio
@patch("services.slack.app.httpx.AsyncClient")
async def test_ask_ucapi_success(MockAsyncClient):
    """
    Tests the ask_ucapi helper function for a successful API call.
    """
    # Arrange: Configure the mock client and its response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "This is a test response."}}]
    }

    # Configure the context manager
    mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
    mock_client_instance.post.return_value = mock_response

    # Act: Call the function
    response = await slack_app.ask_ucapi("ping")

    # Assert: Verify the response is correct
    assert response == "This is a test response."
    mock_client_instance.post.assert_called_once()


@pytest.mark.asyncio
@patch("services.slack.app.httpx.AsyncClient")
async def test_ask_ucapi_http_error(MockAsyncClient):
    """
    Tests how ask_ucapi handles an HTTP status error from the API.
    """
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = slack_app.httpx.HTTPStatusError(
        "Server Error", request=MagicMock(), response=mock_response
    )

    mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
    mock_client_instance.post.return_value = mock_response

    # Act
    response = await slack_app.ask_ucapi("test error")

    # Assert
    assert "Error: Received status 500" in response


@pytest.mark.asyncio
@patch("services.slack.app.httpx.AsyncClient")
async def test_ask_ucapi_request_error(MockAsyncClient):
    """
    Tests how ask_ucapi handles a network request error.
    """
    # Arrange
    mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
    mock_client_instance.post.side_effect = slack_app.httpx.RequestError(
        "Connection failed", request=MagicMock()
    )

    # Act
    response = await slack_app.ask_ucapi("test request error")

    # Assert
    assert "Error: Could not connect to UCAPI" in response