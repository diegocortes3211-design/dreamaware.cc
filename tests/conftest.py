import os
import subprocess
import time
import pytest
import requests

COMPOSE_FILE = os.getenv("COMPOSE_FILE", "tests/docker-compose.yaml")
TARGET_BASE_URL = os.getenv("TARGET_BASE_URL")

@pytest.fixture(scope="session", autouse=True)
def env_setup():
    """
    A session-scoped fixture that starts up the Docker Compose environment
    before any tests run, and tears it down after all tests have completed.
    It can be disabled by setting the TARGET_BASE_URL environment variable,
    allowing tests to run against an external environment.
    """
    if not TARGET_BASE_URL:
        print("Starting Docker Compose services...")
        try:
            subprocess.run(
                ["docker-compose", "-f", COMPOSE_FILE, "up", "-d", "--build"],
                check=True,
                capture_output=True,
                text=True
            )
            # Give services time to become healthy.
            # A more robust solution would be to poll health check endpoints.
            print("Waiting for services to initialize...")
            time.sleep(20)
            print("Services started.")
        except subprocess.CalledProcessError as e:
            print("Failed to start Docker Compose services.")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            pytest.exit("Could not set up the test environment.", 1)

    yield

    if not TARGET_BASE_URL:
        print("Stopping Docker Compose services...")
        subprocess.run(
            ["docker-compose", "-f", COMPOSE_FILE, "down"],
            check=True,
            capture_output=True
        )
        print("Services stopped.")

@pytest.fixture(scope="session")
def base_url():
    """
    Provides the base URL for the gateway service under test.
    """
    return TARGET_BASE_URL or "http://localhost:3001"

@pytest.fixture(scope="session")
def jwks_keys():
    """
    Fetches the JWKS keys from the mock JWKS service.
    """
    jwks_uri = "http://localhost:8001/.well-known/jwks.json"
    try:
        response = requests.get(jwks_uri, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        pytest.fail(f"Could not fetch JWKS keys from {jwks_uri}. Is the mock-jwks service running? Error: {e}")

@pytest.fixture(scope="session")
def private_key():
    """
    Fetches the private key from the mock JWKS service for signing test JWTs.
    """
    pk_uri = "http://localhost:8001/private-key"
    try:
        response = requests.get(pk_uri, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        pytest.fail(f"Could not fetch private key from {pk_uri}. Is the mock-jwks service running? Error: {e}")