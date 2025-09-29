import pytest
from unittest.mock import patch, MagicMock, ANY
from fastapi import FastAPI
from fastapi.testclient import TestClient
from services.action.routes import router as action_router
from services.action.models import PatchResp
from services.action.main import apply_patch, PatchError
import git

# Create a FastAPI app instance for testing the API layer
app = FastAPI()
app.include_router(action_router)
client = TestClient(app)

# --- API Layer Tests ---

def test_api_apply_patch_success():
    """
    Tests a successful call to the /v1/action/patch endpoint.
    This test will be mocked to avoid actual git operations.
    """
    valid_payload = {
        "planId": "plan_f53d2e",
        "stepId": "S1",
        "repo": "dreamaware.cc", # Use a repo that exists
        "branch": "main",
        "diff": "--- a/README.md\n+++ b/README.md\n@@ -1,1 +1,2 @@\n # dreamaware.cc\n+A new line for the test.",
        "commitMessage": "Test commit",
        "author": {"name": "Test Author", "email": "test@example.com"}
    }

    # Mock the underlying apply_patch function to isolate the API test
    with patch('services.action.routes.apply_patch') as mock_apply_patch:
        # Configure the mock to return a future-like object with a result
        mock_response = PatchResp(
            commitSha="mocked_sha_12345",
            signature="mocked_signature_abcde",
            timestamp="2025-01-01T12:00:00Z"
        )
        mock_apply_patch.return_value = mock_response

        response = client.post("/v1/action/patch", json=valid_payload)

        assert response.status_code == 200
        data = response.json()
        assert data["commitSha"] == "mocked_sha_12345"
        assert data["signature"] == "mocked_signature_abcde"
        mock_apply_patch.assert_called_once()


def test_api_apply_patch_validation_error():
    """Tests a call with a missing required field."""
    invalid_payload = {
        "planId": "plan_f53d2e",
        "stepId": "S1",
        "repo": "gateway",
        # 'branch' is missing
        "diff": "--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-a\n+b",
        "commitMessage": "A commit",
        "author": {"name": "test", "email": "test@test.com"}
    }
    response = client.post("/v1/action/patch", json=invalid_payload)
    assert response.status_code == 422
    assert "field required" in response.text

# --- Unit Tests for apply_patch function ---

from unittest.mock import mock_open, call

@pytest.mark.asyncio
@patch('services.action.main.open', new_callable=mock_open)
@patch('services.action.main.tempfile.TemporaryDirectory')
@patch('services.action.main.git.Repo.clone_from')
@patch('services.action.main._create_jws_signature')
async def test_apply_patch_logic_success(mock_create_signature, mock_clone_from, mock_tempdir, mock_open_call):
    """
    Tests the core logic of the apply_patch function with mocks.
    """
    # --- Mock setup ---
    # Configure the TemporaryDirectory mock to return a fake path
    mock_tempdir.return_value.__enter__.return_value = "/fake/temp/dir"

    mock_repo = MagicMock()
    mock_clone_from.return_value = mock_repo

    mock_commit = MagicMock()
    mock_commit.hexsha = "abcdef123456"
    mock_repo.index.commit.return_value = mock_commit

    mock_create_signature.return_value = "generated.jws.signature"

    # --- Call the function ---
    result = await apply_patch(
        planId="plan-1",
        stepId="step-1",
        repo="test-repo",
        branch="main",
        diff="test diff",
        commitMessage="test commit",
        author={"name": "tester", "email": "tester@dev.null"}
    )

    # --- Assertions ---
    mock_clone_from.assert_called_once_with(
        "https://github.com/diegocortes3211-design/test-repo.git", "/fake/temp/dir", branch="main"
    )

    # Assert that the patch file was created and written to
    mock_open_call.assert_called_once_with("/fake/temp/dir/patch.diff", "w")
    mock_open_call().write.assert_called_once_with("test diff")

    # Assert that git apply was called twice (with check and without)
    expected_apply_calls = [
        call('/fake/temp/dir/patch.diff', '--check'),
        call('/fake/temp/dir/patch.diff')
    ]
    mock_repo.git.apply.assert_has_calls(expected_apply_calls)

    # Assert that the commit was called with the correctly formatted message
    args, kwargs = mock_repo.index.commit.call_args
    commit_message_arg = args[0]
    assert "test commit" in commit_message_arg
    assert "Plan: plan-1" in commit_message_arg
    assert "Step: step-1" in commit_message_arg

    mock_create_signature.assert_called_once()

    assert result.commitSha == "abcdef123456"
    assert result.signature == "generated.jws.signature"

@pytest.mark.asyncio
@patch('services.action.main.tempfile.TemporaryDirectory')
@patch('services.action.main.git.Repo.clone_from')
async def test_apply_patch_git_error(mock_clone_from, mock_tempdir):
    """
    Tests that PatchError is raised when a git command fails.
    """
    # --- Mock setup ---
    mock_clone_from.side_effect = git.GitCommandError("clone", "fatal: repository not found")

    # --- Call and assert exception ---
    with pytest.raises(PatchError, match="Git operation failed"):
        await apply_patch(
            planId="plan-2",
            stepId="step-2",
            repo="nonexistent-repo",
            branch="master",
            diff="a diff",
            commitMessage="a message",
            author={"name": "err", "email": "err@dev.null"}
        )