import os

# Set a dummy API key BEFORE importing the adapter module
# This prevents the module from raising an error on import
os.environ["CURSOR_API_KEY"] = "test-key"

import pytest
from unittest.mock import patch, MagicMock
from services.llm_adapters import cursor_pro

@pytest.fixture
def adapter():
    """Provides a CursorProAdapter instance for testing."""
    return cursor_pro.CursorProAdapter()

@pytest.mark.asyncio
@patch("services.llm_adapters.cursor_pro.httpx.AsyncClient")
async def test_chat_success(MockAsyncClient, adapter):
    """Tests the chat method for a successful API call."""
    # Arrange
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Cursor chat response"}}]
    }

    mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
    mock_client_instance.post.return_value = mock_response

    # Act
    response = await adapter.chat([{"role": "user", "content": "hello"}])

    # Assert
    assert response["choices"][0]["message"]["content"] == "Cursor chat response"
    mock_client_instance.post.assert_called_once()

@pytest.mark.asyncio
@patch("services.llm_adapters.cursor_pro.httpx.AsyncClient")
async def test_generate_code_success(MockAsyncClient, adapter):
    """Tests the generate_code method."""
    # Arrange
    mock_response_json = {
        "choices": [{"message": {"content": "print('Hello, World!')"}}]
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_json

    mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
    mock_client_instance.post.return_value = mock_response

    # Act
    code = await adapter.generate_code("A simple hello world in Python")

    # Assert
    assert code == "print('Hello, World!')"

@patch.dict(os.environ, {"CURSOR_API_KEY": ""}, clear=True)
def test_adapter_init_no_key():
    """
    Tests that the adapter raises a ValueError if the API key is not set.
    We patch the environment for this specific test.
    """
    with pytest.raises(ValueError, match="CURSOR_API_KEY not set"):
        # We need to re-import the module within the patched context
        # to see the change in the environment variable.
        import importlib
        importlib.reload(cursor_pro)
        cursor_pro.CursorProAdapter()
    # Reload again to restore the original state for other tests
    importlib.reload(cursor_pro)