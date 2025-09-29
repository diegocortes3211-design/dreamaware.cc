import pytest
from pathlib import Path
import yaml
from services.agentics.orchestrator import Orchestrator

@pytest.fixture
def orchestrator(tmp_path: Path) -> Orchestrator:
    """
    Creates an Orchestrator instance with a temporary config file for isolated testing.
    This fixture copies the real config into a temporary directory to ensure that
    tests are repeatable and don't depend on the global state of the repository.
    """
    # Define the path to the actual config file
    real_config_path = Path(__file__).resolve().parents[1] / "configs" / "syzygy_matrix.yaml"
    config_content = real_config_path.read_text(encoding="utf-8")

    # Create a temporary config file with the same content
    temp_config_path = tmp_path / "syzygy_matrix.yaml"
    temp_config_path.write_text(config_content)

    # Return an orchestrator instance that uses the temporary config
    return Orchestrator(config_path=temp_config_path)

def test_load_matrix_successfully(orchestrator: Orchestrator):
    """
    Tests that the Syzygy Matrix loads and validates correctly.
    It checks that the top-level keys ('agents', 'data_flows') are present
    and that the 'Executive' agent is defined, as per the configuration.
    """
    matrix = orchestrator.load_matrix()
    assert "Executive" in matrix.agents
    assert "Action" in matrix.agents
    assert isinstance(matrix.data_flows, list)
    print("Test passed: The Syzygy Matrix was loaded and validated successfully.")

def test_route_valid_data_flow(orchestrator: Orchestrator):
    """
    Tests that a valid data flow, as defined in the Syzygy Matrix, is permitted.
    It uses a known valid flow from the configuration ('Executive' to 'Action')
    and asserts that no exception is raised.
    """
    matrix = orchestrator.load_matrix()
    # Select a known valid data flow from the configuration
    valid_flow = next(flow for flow in matrix.data_flows if flow['from'] == 'Executive' and flow['to'] == 'Action')
    from_role, to_role = valid_flow["from"], valid_flow["to"]

    # This should execute without raising an exception
    orchestrator.route_message(from_role, to_role, {"data": "test payload"})
    print(f"Test passed: Valid data flow from '{from_role}' to '{to_role}' was correctly permitted.")

def test_route_invalid_data_flow_raises_error(orchestrator: Orchestrator):
    """
    Tests that an invalid data flow, one not defined in the Syzygy Matrix,
    is correctly denied by raising a ValueError. This is a critical security test.
    """
    orchestrator.load_matrix()
    # Define a flow that is explicitly not in the configuration (e.g., Action to Executive)
    from_role, to_role = "Action", "Executive"

    with pytest.raises(ValueError, match=f"Data flow from '{from_role}' to '{to_role}' is not permitted"):
        orchestrator.route_message(from_role, to_role, {"status": "unauthorized attempt"})
    print(f"Test passed: Invalid data flow from '{from_role}' to '{to_role}' was correctly denied.")

def test_register_known_agent_succeeds(orchestrator: Orchestrator):
    """
    Tests that a valid agent role from the Syzygy Matrix can be successfully registered.
    """
    orchestrator.load_matrix()
    class MockExecutiveAgent: pass

    # This should not raise an exception
    orchestrator.register_agents({"Executive": MockExecutiveAgent})
    print("Test passed: A known agent role was successfully registered.")

def test_register_unknown_agent_raises_error(orchestrator: Orchestrator):
    """
    Tests that attempting to register an agent with a role not defined in the
    Syzygy Matrix raises a KeyError.
    """
    orchestrator.load_matrix()
    class MockUnknownAgent: pass

    with pytest.raises(KeyError, match="Agent role 'UnknownAgent' is not defined"):
        orchestrator.register_agents({"UnknownAgent": MockUnknownAgent})
    print("Test passed: Attempting to register an unknown agent role correctly raised an error.")