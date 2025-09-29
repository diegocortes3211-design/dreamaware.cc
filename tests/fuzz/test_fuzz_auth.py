import pytest
import requests
from hypothesis import given, strategies as st, settings

# Define Hypothesis strategies for generating various kinds of data.
# We'll generate random text for most fields to test for parsing errors.
fuzz_text = st.text(min_size=1, max_size=200)
fuzz_body = st.dictionaries(keys=st.text(), values=st.text())

@pytest.mark.fuzzing
@settings(deadline=1000, max_examples=50) # Keep the number of examples low for CI speed
@given(
    token=fuzz_text,
    hmac_kid=fuzz_text,
    hmac_sig=fuzz_text,
    hmac_ts=fuzz_text,
    hmac_nonce=fuzz_text,
    body=fuzz_body
)
def test_fuzz_auth_endpoint_handles_garbage_input(base_url, token, hmac_kid, hmac_sig, hmac_ts, hmac_nonce, body):
    """
    Fuzzes the protected endpoint with a wide range of malformed inputs.
    The primary goal is to ensure the server does not crash (e.g., return a 500 error)
    and gracefully handles unexpected or invalid data by returning a 4xx client error.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "X-HMAC-KID": hmac_kid,
        "X-HMAC-SIG": hmac_sig,
        "X-HMAC-TS": hmac_ts,
        "X-HMAC-NONCE": hmac_nonce,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{base_url}/v1/protected",
            headers=headers,
            json=body,
            timeout=5 # Prevent tests from hanging
        )
        # The server should gracefully reject garbage input.
        # A 401 Unauthorized or 400 Bad Request is expected.
        # A 5xx server error indicates a crash or unhandled exception.
        assert response.status_code < 500, f"Server returned a 5xx error on unexpected input: {response.text}"
        assert response.status_code != 200, "Server should not succeed with garbage input"

    except requests.RequestException:
        # Timeouts or connection errors are acceptable failures in a fuzzing context,
        # as they don't indicate a server crash.
        pass