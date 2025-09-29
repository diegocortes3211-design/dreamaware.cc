import pytest
import subprocess
import time
import requests
from .helpers import generate_jwt, get_container_id

def partition_network(container_id, network_name="tests_default"):
    """
    Creates a network partition by disconnecting a container from the network.
    """
    print(f"Creating network partition for container {container_id} on network {network_name}...")
    try:
        subprocess.run(
            ["docker", "network", "disconnect", network_name, container_id],
            check=True, capture_output=True,
        )
        print(f"Network partition created for {container_id}.")
    except subprocess.CalledProcessError:
        # Fallback for default bridge network name
        print("Falling back to 'bridge' network...")
        subprocess.run(
            ["docker", "network", "disconnect", "bridge", container_id],
            check=True, capture_output=True,
        )

def heal_network(container_id, network_name="tests_default"):
    """
    Heals the network partition by reconnecting a container to the network.
    """
    print(f"Healing network partition for container {container_id} on network {network_name}...")
    try:
        subprocess.run(
            ["docker", "network", "connect", network_name, container_id],
            check=True, capture_output=True,
        )
        print(f"Network partition healed for {container_id}.")
    except subprocess.CalledProcessError:
        print("Falling back to 'bridge' network...")
        subprocess.run(
            ["docker", "network", "connect", "bridge", container_id],
            check=True, capture_output=True,
        )


def test_jti_consistency_during_split_brain(base_url, private_key):
    """
    Tests that a JTI cannot be used on two separate 'primaries' during a split-brain scenario.
    """
    jti = "jti-split-brain-test-1"
    token = generate_jwt(private_key, {"jti": jti, "sub": "user456"})
    headers = {"Authorization": f"Bearer {token}"}

    primary_container_id = get_container_id("redis-primary")

    try:
        # 1. Isolate the primary Redis node.
        partition_network(primary_container_id)

        # 2. Wait for Sentinel to promote a new one.
        print("Waiting for Sentinel to react to the partition...")
        time.sleep(15)

        # 3. Send a request. This should go to the newly promoted primary and succeed.
        print("Sending request to the new primary (post-partition)...")
        # Use a helper that includes HMAC headers for the mock gateway
        from .test_replay_and_skew import make_signed_request
        resp1 = make_signed_request(base_url, token, "nonce-split-1", body={"data": "request_to_new_primary"})
        assert resp1.status_code == 200, f"Request to the new primary failed with status {resp1.status_code}. Body: {resp1.text}"
        print("Request to new primary was successful.")

        # 4. Heal the network partition. The old primary comes back online.
        heal_network(primary_container_id)
        print("Waiting for network to stabilize...")
        time.sleep(10)

        # 5. Attempt to replay the same token. This should be rejected.
        print(f"Attempting to replay request with JTI: {jti} after healing...")
        resp2 = make_signed_request(base_url, token, "nonce-split-2", body={"data": "replay_after_heal"})
        assert resp2.status_code == 401, f"Expected replayed request to be rejected with 401, but got {resp2.status_code}"

        error_data = resp2.json()
        assert error_data.get("error") == "jti_replayed", f"Expected 'jti_replayed' error, but got: {error_data}"
        print("Replay successfully rejected after network heal.")
    finally:
        # Ensure the network is always healed, even if the test fails.
        heal_network(primary_container_id)