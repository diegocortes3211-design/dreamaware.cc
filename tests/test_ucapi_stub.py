import pytest
from unittest.mock import AsyncMock, patch
from services.slack.app import ask_ucapi

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

@patch('services.slack.app.httpx.AsyncClient')
async def test_ask_ucapi_success(mock_client):
    """
    Tests the ask_ucapi function for a successful API call.
    """
    # Mock the response from the UCAPI
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "This is a test response."}}]
    }
    mock_response.raise_for_status.return_value = None

    # Configure the mock client to return the mock response
    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

    # Call the function
    prompt = "Hello, UCAPI!"
    response = await ask_ucapi(prompt)

    # Assert the response is what we expect
    assert response == "This is a test response."
    # Verify that post was called correctly
    mock_client.return_value.__aenter__.return_value.post.assert_called_once()

@patch('services.slack.app.httpx.AsyncClient')
async def test_ask_ucapi_http_error(mock_client):
    """
    Tests the ask_ucapi function for an HTTP error from the API.
    """
    # Mock an error response
    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.raise_for_status.side_effect = Exception("HTTP 500")

    mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

    prompt = "This should fail."
    response = await ask_ucapi(prompt)

    assert "Error calling UCAPI" in response

@patch('services.slack.app.UCAPI_URL', None)
def test_ask_ucapi_not_configured():
    """
    Tests the ask_ucapi function when the service is not configured.
    """
    import asyncio
    response = asyncio.run(ask_ucapi("test"))
    assert "UCAPI is not configured" in response