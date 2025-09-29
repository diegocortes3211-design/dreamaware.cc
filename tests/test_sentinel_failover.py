import pytest
import subprocess
import time
import requests
from .helpers import generate_jwt, get_container_id

def kill_primary_redis():
    """
    Simulates a failure of the primary Redis node by killing the container.
    """
    primary_container_id = get_container_id("redis-primary")
    print(f"Killing primary Redis container (ID: {primary_container_id})...")
    try:
        subprocess.run(
            ["docker", "kill", primary_container_id],
            check=True,
            capture_output=True,
        )
        print("Primary Redis container killed.")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Failed to kill primary Redis container {primary_container_id}. Error: {e.stderr.decode()}")


def test_jti_replay_is_prevented_after_failover(base_url, private_key):
    """
    Tests that a JWT with a specific JTI (JWT ID) cannot be replayed
    even after a Redis Sentinel failover event.
    """
    # 1. Generate a token with a unique JTI.
    jti = "jti-failover-test-1"
    token = generate_jwt(private_key, {"jti": jti, "sub": "user123"})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Make a first, successful request to use the JTI.
    print(f"Making initial request with JTI: {jti}")
    resp1 = requests.post(f"{base_url}/v1/protected", headers=headers, json={"data": "initial"})
    assert resp1.status_code == 200, f"Expected first request to be successful, but got {resp1.status_code}"
    print("Initial request successful.")

    # 3. Simulate a primary Redis node failure.
    kill_primary_redis()

    # 4. Wait for Sentinel to perform the failover (e.g., 10-15 seconds).
    print("Waiting for Sentinel to elect a new primary...")
    time.sleep(15)
    print("Failover period has passed.")

    # 5. Attempt to replay the same token. This request should be rejected.
    print(f"Attempting to replay request with JTI: {jti}")
    resp2 = requests.post(f"{base_url}/v1/protected", headers=headers, json={"data": "replay"})
    assert resp2.status_code == 401, f"Expected replayed request to be rejected with 401, but got {resp2.status_code}"

    # Assuming the gateway returns a specific error for replayed JTIs.
    error_data = resp2.json()
    assert error_data.get("error") == "jti_replayed", f"Expected 'jti_replayed' error, but got: {error_data}"
    print("Replay successfully rejected after failover.")