import pytest
from unittest.mock import AsyncMock, patch
from services.llm_adapters import cursor_pro

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

@patch('services.llm_adapters.cursor_pro.client')
async def test_chat_success(mock_client):
    """
    Tests the chat function for a successful API call to Cursor.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Cursor response"}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response

    messages = [{"role": "user", "content": "Hello Cursor"}]
    response = await cursor_pro.chat(messages)

    assert response["choices"][0]["message"]["content"] == "Cursor response"
    mock_client.post.assert_called_once()

@patch('services.llm_adapters.cursor_pro.client')
async def test_generate_code_success(mock_client):
    """
    Tests the generate_code helper for a successful generation.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "def hello():\n    print('Hello World')"}}]
    }
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response

    prompt = "write a hello world function in python"
    code = await cursor_pro.generate_code(prompt)

    assert "def hello()" in code
    # The system prompt is added, so the messages will have 2 items
    call_args = mock_client.post.call_args.kwargs['json']
    assert len(call_args['messages']) == 2
    assert call_args['messages'][1]['content'] == prompt

@patch('services.llm_adapters.cursor_pro.client')
async def test_chat_http_error(mock_client):
    """
    Tests that an HTTP error is raised correctly.
    """
    mock_client.post.side_effect = Exception("API Error")

    with pytest.raises(Exception, match="API Error"):
        await cursor_pro.chat([{"role": "user", "content": "test"}])

@patch('services.llm_adapters.cursor_pro.client')
async def test_generate_code_parsing_error(mock_client):
    """
    Tests that a parsing error in the response is handled gracefully.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200
    # Malformed response
    mock_response.json.return_value = {"choices": []}
    mock_response.raise_for_status.return_value = None
    mock_client.post.return_value = mock_response

    response = await cursor_pro.generate_code("test")
    assert "Error: Could not parse the response" in response