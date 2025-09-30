import pytest
import os
from unittest.mock import patch, AsyncMock

from services.ucapi.adapters.openai_adapter import OpenAIAdapter, OPENAI_KEY_ENV

@pytest.fixture
def openai_adapter():
    """Fixture to provide an OpenAIAdapter instance."""
    return OpenAIAdapter()

@pytest.mark.asyncio
async def test_openai_adapter_no_api_key(openai_adapter):
    """Tests that a RuntimeError is raised if the API key is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(RuntimeError, match=f"{OPENAI_KEY_ENV} is not set."):
            await openai_adapter.chat(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                tools=None,
                tool_choice=None,
                params={},
                stream=False,
            )

@pytest.mark.asyncio
@patch("services.ucapi.adapters.openai_adapter.httpx.AsyncClient")
async def test_openai_adapter_non_streaming(MockAsyncClient, openai_adapter):
    """Tests the OpenAI adapter in non-streaming mode."""
    mock_response_data = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4o-mini",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hello there"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 9, "completion_tokens": 12, "total_tokens": 21}
    }

    # Configure the mock response object returned by the post call
    mock_response = AsyncMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json = AsyncMock(return_value=mock_response_data)

    # Configure the client instance that is entered by 'async with'
    mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
    mock_client_instance.post.return_value = mock_response

    with patch.dict(os.environ, {OPENAI_KEY_ENV: "test-key"}):
        response = await openai_adapter.chat(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}],
            tools=None,
            tool_choice=None,
            params={},
            stream=False,
        )

    assert response == mock_response_data
    mock_client_instance.post.assert_called_once()
    call_payload = mock_client_instance.post.call_args.kwargs['json']
    assert call_payload['stream'] is False


@pytest.mark.asyncio
async def test_openai_adapter_streaming_value_error(openai_adapter):
    """Tests that a ValueError is raised in streaming mode if stream_cb is not provided."""
    with patch.dict(os.environ, {OPENAI_KEY_ENV: "test-key"}):
        with pytest.raises(ValueError, match="stream_cb must be provided for streaming mode."):
            await openai_adapter.chat(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                tools=None,
                tool_choice=None,
                params={},
                stream=True,
                stream_cb=None,
            )