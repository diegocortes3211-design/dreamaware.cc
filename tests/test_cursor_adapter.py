import pytest
import httpx
from unittest.mock import AsyncMock, patch

# Make sure the functions can be imported
from services.llm_adapters.cursor_pro import chat, generate_code

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_chat_success(mock_client):
    """
    Tests the chat function with a mocked successful API response.
    """
    mock_response_payload = {
        "choices": [{"message": {"content": "Hello, world!"}}]
    }
    mock_request = httpx.Request("POST", "http://dummy.url")
    mock_response = httpx.Response(200, json=mock_response_payload, request=mock_request)
    mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

    messages = [{"role": "user", "content": "Say hi"}]
    response_data = await chat(messages)

    assert response_data == mock_response_payload
    mock_client.return_value.__aenter__.return_value.post.assert_called_once()
    call_args = mock_client.return_value.__aenter__.return_value.post.call_args
    assert call_args.kwargs["json"]["messages"] == messages

@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_chat_http_error(mock_client):
    """
    Tests that the chat function raises an exception on HTTP error.
    """
    mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.HTTPStatusError(
        "Bad Gateway", request=AsyncMock(), response=httpx.Response(502)
    )

    with pytest.raises(httpx.HTTPStatusError):
        await chat([{"role": "user", "content": "test"}])

@pytest.mark.asyncio
@patch("services.llm_adapters.cursor_pro.chat")
async def test_generate_code_success(mock_chat):
    """
    Tests the generate_code helper function.
    """
    mock_chat.return_value = {
        "choices": [{"message": {"content": "print('Hello, world!')"}}]
    }

    code = await generate_code("Create a hello world script in Python")

    assert code == "print('Hello, world!')"
    mock_chat.assert_called_once()

@pytest.mark.asyncio
@patch("services.llm_adapters.cursor_pro.chat")
async def test_generate_code_api_failure(mock_chat):
    """
    Tests that generate_code handles exceptions from the chat function.
    """
    mock_chat.side_effect = Exception("API connection failed")

    response = await generate_code("prompt")

    assert "An unexpected error occurred" in response
    assert "API connection failed" in response