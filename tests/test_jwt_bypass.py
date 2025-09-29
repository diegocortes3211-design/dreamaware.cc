import pytest
import requests
from jose import jwt
from .helpers import generate_jwt

def test_alg_none_attack_is_rejected(base_url, private_key):
    """
    Tests that a JWT with the "alg" header set to "none" is rejected.
    This is a classic JWT vulnerability. The server must not trust the token's
    header to determine the verification algorithm.
    """
    # 1. Create a valid payload.
    payload = {
        "iss": "test-issuer",
        "sub": "user-alg-none",
        "jti": "jti-alg-none-1",
        "exp": 9999999999, # A far-future expiration
    }

    # 2. Manually encode the token with "alg": "none" and no signature.
    # The `jsonwebtoken` library doesn't allow creating "alg=none" tokens directly
    # for security reasons, so we construct it manually.
    unsigned_token = jwt.encode(payload, key=None, algorithm='none')

    headers = {"Authorization": f"Bearer {unsigned_token}"}

    # 3. The gateway should reject this token.
    # The HMAC middleware will fail first because the JWT middleware would reject it.
    # We will send a request that would otherwise pass HMAC checks.
    # But the JWT validation should catch it before HMAC is even checked.
    # For this test, we can omit the HMAC headers as the JWT check comes first.
    print("Sending request with alg=none token...")
    resp = requests.post(f"{base_url}/v1/protected", headers=headers, json={})

    assert resp.status_code == 401, f"Expected alg=none token to be rejected with 401, but got {resp.status_code}"

    error_data = resp.json()
    assert "invalid_jwt" in error_data.get("error", ""), f"Expected 'invalid_jwt' error, but got: {error_data}"
    print("alg=none token successfully rejected.")


def test_signature_stripping_is_rejected(base_url, private_key):
    """
    Tests that a token with a valid payload but a stripped signature is rejected.
    """
    # 1. Generate a valid token.
    token = generate_jwt(private_key, {"sub": "user-sig-strip"})

    # 2. Strip the signature part (the last part after a dot).
    parts = token.split('.')
    token_with_stripped_sig = f"{parts[0]}.{parts[1]}." # Keep the trailing dot

    headers = {"Authorization": f"Bearer {token_with_stripped_sig}"}

    print("Sending request with stripped signature token...")
    resp = requests.post(f"{base_url}/v1/protected", headers=headers, json={})

    assert resp.status_code == 401, f"Expected stripped signature token to be rejected with 401, but got {resp.status_code}"
    error_data = resp.json()
    assert "invalid_jwt" in error_data.get("error", ""), f"Expected 'invalid_jwt' error, but got: {error_data}"
    print("Token with stripped signature successfully rejected.")