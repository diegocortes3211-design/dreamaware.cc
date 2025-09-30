import pytest
import httpx
from unittest.mock import AsyncMock, patch

# Make sure the app can be imported
from services.slack.app import ask_ucapi

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_ask_ucapi_success(mock_client):
    """
    Tests that ask_ucapi correctly calls the UCAPI endpoint
    and processes a successful response.
    """
    # Mock the response from the UCAPI service
    mock_request = httpx.Request("POST", "http://dummy.url")
    mock_response = httpx.Response(
        200,
        json={
            "choices": [{
                "message": {
                    "content": "pong"
                }
            }]
        },
        request=mock_request
    )
    mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

    # Call the function
    response_text = await ask_ucapi("ping")

    # Assert the response is correct
    assert response_text == "pong"

    # Assert that the post method was called with the correct parameters
    mock_client.return_value.__aenter__.return_value.post.assert_called_once()
    call_args = mock_client.return_value.__aenter__.return_value.post.call_args
    assert "ping" in call_args.kwargs["json"]["messages"][0]["content"]


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_ask_ucapi_http_error(mock_client):
    """
    Tests that ask_ucapi handles an HTTP error gracefully.
    """
    # Mock an error response
    mock_request = httpx.Request("POST", "http://dummy.url")
    mock_response = httpx.Response(500, request=mock_request)
    mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.HTTPStatusError(
        "Internal Server Error", request=mock_request, response=mock_response
    )

    response_text = await ask_ucapi("test")

    assert "Error communicating with UCAPI" in response_text
    assert "500" in response_text