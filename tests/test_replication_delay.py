import pytest
import requests
import subprocess
import time
from .helpers import generate_jwt, get_container_id

def disconnect_replica(container_id, network_name="tests_default"):
    """Disconnects a replica from the network."""
    print(f"Disconnecting replica {container_id} from network...")
    try:
        subprocess.run(
            ["docker", "network", "disconnect", network_name, container_id],
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            ["docker", "network", "disconnect", "bridge", container_id],
            check=True, capture_output=True, text=True
        )

def connect_replica(container_id, network_name="tests_default"):
    """Reconnects a replica to the network."""
    print(f"Reconnecting replica {container_id} to network...")
    try:
        subprocess.run(
            ["docker", "network", "connect", network_name, container_id],
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError:
        subprocess.run(
            ["docker", "network", "connect", "bridge", container_id],
            check=True, capture_output=True, text=True
        )

@pytest.mark.skip(reason="Requires `min-replicas-to-write 2` configured on Redis primary to be effective.")
def test_gateway_fails_closed_when_replication_guarantees_are_not_met(base_url, private_key):
    """
    Tests that the gateway fails gracefully when Redis cannot meet replication guarantees.
    NOTE: Requires Redis primary to be configured with `min-replicas-to-write 2`.
    """
    from .test_replay_and_skew import make_signed_request
    replica1_id = get_container_id("redis-replica1")

    try:
        # 1. Initial request should succeed.
        token1 = generate_jwt(private_key, {"sub": "user-repl-delay-1", "jti": "jti-repl-1"})
        resp1 = make_signed_request(base_url, token1, "nonce-repl-1")
        assert resp1.status_code == 200, f"Initial request should succeed, but got {resp1.status_code}"

        # 2. Disconnect one of the two replicas.
        disconnect_replica(replica1_id)
        time.sleep(5)

        # 3. Next request should fail as `min-replicas-to-write` is not met.
        token2 = generate_jwt(private_key, {"sub": "user-repl-delay-2", "jti": "jti-repl-2"})
        resp2 = make_signed_request(base_url, token2, "nonce-repl-2")
        assert resp2.status_code >= 500, f"Expected a server error, but got {resp2.status_code}"
        print("Gateway correctly failed closed when replication quorum was lost.")

    finally:
        # 4. Reconnect the replica to clean up.
        connect_replica(replica1_id)
        print("Waiting for service to recover...")
        time.sleep(10)

        # Verify recovery
        token3 = generate_jwt(private_key, {"sub": "user-repl-delay-3", "jti": "jti-repl-3"})
        resp3 = make_signed_request(base_url, token3, "nonce-repl-3")
        assert resp3.status_code == 200, f"Expected service to recover, but got {resp3.status_code}"
        print("Service recovered successfully.")