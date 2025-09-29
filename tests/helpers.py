import time
import json
import hashlib
import hmac
import subprocess
import pytest
from jose import jwt

def get_container_id(service_name: str) -> str:
    """
    Gets the running container ID for a given docker-compose service.
    """
    compose_file = "tests/docker-compose.yaml"
    try:
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "ps", "-q", service_name],
            check=True,
            capture_output=True,
            text=True,
        )
        container_id = result.stdout.strip()
        if not container_id:
            pytest.fail(f"Could not get container ID for service '{service_name}'. Is it running?")
        return container_id
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to get container ID for service '{service_name}'. Error: {e.stderr}")
    except FileNotFoundError:
        pytest.fail("`docker-compose` command not found. Is Docker installed and in the PATH?")


def generate_jwt(private_key: dict, claims: dict, headers: dict = None) -> str:
    """
    Generates a JWT using the provided private key and claims.
    """
    if not headers:
        headers = {"kid": private_key.get("kid", "test-key-1")}

    # Add standard claims if they are not provided
    if "exp" not in claims:
        claims["exp"] = int(time.time()) + 60  # Expires in 60 seconds
    if "iat" not in claims:
        claims["iat"] = int(time.time())
    if "iss" not in claims:
        claims["iss"] = "test-issuer"

    return jwt.encode(claims, private_key, algorithm="RS256", headers=headers)


def create_hmac_signature(
    secret: str,
    method: str,
    path: str,
    query_params: str,
    timestamp: int,
    nonce: str,
    body: dict
) -> str:
    """
    Creates a canonical HMAC-SHA256 signature string.
    The canonicalization process must match the server's implementation exactly.
    """
    # 1. Canonicalize the body: sort keys, remove whitespace.
    # This is a common and robust way to canonicalize JSON.
    canonical_body = json.dumps(body, separators=(",", ":"), sort_keys=True)
    body_hash = hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()

    # 2. Construct the string to sign.
    string_to_sign = "\n".join([
        method.upper(),
        path,
        query_params, # Should be canonicalized as well if used
        str(timestamp),
        nonce,
        body_hash,
    ])

    # 3. Create the HMAC signature.
    signature = hmac.new(
        secret.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return signature