import pytest
import time
import requests
from .helpers import generate_jwt, create_hmac_signature

def make_signed_request(base_url, token, nonce, body=None, timestamp_offset=0):
    """
    Helper function to construct and send an HMAC-signed request.
    """
    body = body or {}
    timestamp = int(time.time()) + timestamp_offset

    signature = create_hmac_signature(
        secret="topsecret123", # This should match the gateway's secret
        method="POST",
        path="/v1/protected",
        query_params="", # Assuming no query params for this endpoint
        timestamp=timestamp,
        nonce=nonce,
        body=body
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "X-HMAC-KID": "default",
        "X-HMAC-SIG": signature,
        "X-HMAC-TS": str(timestamp),
        "X-HMAC-NONCE": nonce
    }

    return requests.post(f"{base_url}/v1/protected", headers=headers, json=body)


def test_hmac_replay_is_rejected(base_url, private_key):
    """
    Tests that replaying a request with the same nonce is rejected.
    """
    token = generate_jwt(private_key, {"sub": "user789"})
    nonce = "nonce-replay-test-1"

    # 1. First request should succeed.
    print("Making first request with nonce:", nonce)
    resp1 = make_signed_request(base_url, token, nonce)
    assert resp1.status_code == 200, f"Expected first request to succeed, but got {resp1.status_code}"
    print("First request successful.")

    # 2. Replaying the request immediately with the same nonce should fail.
    print("Replaying request with the same nonce...")
    resp2 = make_signed_request(base_url, token, nonce)
    assert resp2.status_code == 401, f"Expected replayed request to fail with 401, but got {resp2.status_code}"

    error_data = resp2.json()
    assert error_data.get("error") == "nonce_replayed", f"Expected 'nonce_replayed' error, but got: {error_data}"
    print("Replay successfully rejected.")


def test_request_outside_skew_window_is_rejected(base_url, private_key):
    """
    Tests that a request with a timestamp far in the past or future is rejected.
    """
    token = generate_jwt(private_key, {"sub": "user789"})

    # 1. Test with a timestamp far in the past (e.g., 10 minutes ago).
    # SKEW_WINDOW_SEC is 300s (5 mins), so this should be rejected.
    print("Sending request with timestamp from 10 minutes ago...")
    resp_past = make_signed_request(base_url, token, "nonce-past-test", timestamp_offset=-600)
    assert resp_past.status_code == 401, f"Expected past request to fail with 401, but got {resp_past.status_code}"
    error_data_past = resp_past.json()
    assert error_data_past.get("error") == "timestamp_out_of_range", f"Expected 'timestamp_out_of_range' error, but got: {error_data_past}"
    print("Request with past timestamp successfully rejected.")

    # 2. Test with a timestamp far in the future.
    print("Sending request with timestamp from 10 minutes in the future...")
    resp_future = make_signed_request(base_url, token, "nonce-future-test", timestamp_offset=600)
    assert resp_future.status_code == 401, f"Expected future request to fail with 401, but got {resp_future.status_code}"
    error_data_future = resp_future.json()
    assert error_data_future.get("error") == "timestamp_out_of_range", f"Expected 'timestamp_out_of_range' error, but got: {error_data_future}"
    print("Request with future timestamp successfully rejected.")