import pytest
import time
import requests
import json
from .helpers import generate_jwt, create_hmac_signature

def test_hmac_rejects_different_canonical_forms(base_url, private_key):
    """
    Tests that the HMAC signature validation is strict about the canonical
    form of the JSON body. A signature created over a body with reordered keys
    should not be valid for the same body with a different key order.
    """
    token = generate_jwt(private_key, {"sub": "user-canon-test"})
    nonce = "nonce-canon-test-1"
    timestamp = int(time.time())

    # 1. Create two versions of the body with the same data but different key order.
    body1 = {"a": 1, "b": 2}
    body2 = {"b": 2, "a": 1}

    # 2. Generate a signature based on the canonical form of body1.
    # The helper function must use a consistent canonicalization (e.g., sorted keys, no spaces).
    signature = create_hmac_signature(
        secret="topsecret123",
        method="POST",
        path="/v1/protected",
        query_params="",
        timestamp=timestamp,
        nonce=nonce,
        body=body1
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "X-HMAC-KID": "default",
        "X-HMAC-SIG": signature,
        "X-HMAC-TS": str(timestamp),
        "X-HMAC-NONCE": nonce,
        "Content-Type": "application/json"
    }

    # 3. The request with body1 should succeed because the signature was generated for it.
    print("Sending request with original body and signature...")
    resp1 = requests.post(f"{base_url}/v1/protected", headers=headers, json=body1)
    assert resp1.status_code == 200, f"Expected request with original body to succeed, but got {resp1.status_code}"
    print("Request with original body was successful.")

    # 4. The request with body2 should FAIL, because even though the data is the same,
    #    its canonical representation is different, which should result in a different hash
    #    on the server side, thus invalidating the signature.
    print("Sending request with reordered body and the same signature...")
    resp2 = requests.post(f"{base_url}/v1/protected", headers=headers, json=body2)
    assert resp2.status_code == 401, f"Expected request with reordered body to fail with 401, but got {resp2.status_code}"

    error_data = resp2.json()
    assert error_data.get("error") == "invalid_signature", f"Expected 'invalid_signature' error, but got: {error_data}"
    print("Request with reordered body was successfully rejected.")