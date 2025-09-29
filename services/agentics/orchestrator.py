from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, Type, Optional
from pydantic import BaseModel, ValidationError

# Correctly locate the config file relative to this script's location
CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "syzygy_matrix.yaml"

class SyzygyMatrix(BaseModel):
    """Pydantic model to validate the structure of the Syzygy Matrix configuration."""
    agents: Dict[str, Dict[str, Any]]
    data_flows: list

class Orchestrator:
    """
    The Orchestrator is the central nervous system of the agentic architecture.
    It loads the Syzygy Matrix configuration, validates it, and enforces the
    defined data flow rules for inter-agent communication.
    """
    def __init__(self, config_path: Path = CONFIG_PATH):
        """
        Initializes the Orchestrator with the path to the Syzygy Matrix config.
        """
        self.config_path = config_path
        self.matrix: Optional[SyzygyMatrix] = None
        self.agent_map: Dict[str, Type] = {}  # Maps agent roles to their classes

    def load_matrix(self) -> SyzygyMatrix:
        """
        Loads and validates the Syzygy Matrix YAML file against the Pydantic model.
        Raises a ValidationError if the configuration is invalid.
        """
        raw_config = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        try:
            self.matrix = SyzygyMatrix(**raw_config)
        except ValidationError as e:
            # Provide a clear error message if validation fails
            print(f"Syzygy Matrix validation error: {e}")
            raise
        print("Syzygy Matrix loaded and validated successfully.")
        return self.matrix

    def register_agents(self, agent_classes: Dict[str, Type]) -> None:
        """
        Registers agent classes with the orchestrator.
        Ensures that all registered agent roles are defined in the Syzygy Matrix.
        """
        if not self.matrix:
            raise RuntimeError("Matrix must be loaded before registering agents.")

        for role in agent_classes:
            if role not in self.matrix.agents:
                raise KeyError(f"Agent role '{role}' is not defined in the Syzygy Matrix.")
        self.agent_map = agent_classes
        print(f"Registered agents: {list(agent_classes.keys())}")

    def route_message(self, from_role: str, to_role: str, payload: Any) -> None:
        """
        Routes a message from one agent to another, enforcing data flow rules.
        This is a critical security gate that prevents unauthorized inter-agent communication.
        """
        if not self.matrix:
            raise RuntimeError("Matrix must be loaded before routing messages.")

        # Check if the data flow is permitted by the Syzygy Matrix
        is_permitted = any(
            flow["from"] == from_role and flow["to"] == to_role
            for flow in self.matrix.data_flows
        )

        if not is_permitted:
            raise ValueError(f"Data flow from '{from_role}' to '{to_role}' is not permitted by the Syzygy Matrix.")

        # In a real system, this would integrate with a message queue (e.g., Redis, RabbitMQ).
        # For now, it's a placeholder that prints the routing information.
        print(f"Routing message from '{from_role}' to '{to_role}': {payload}")

# Example usage block, can be expanded for testing or as a CLI entrypoint
if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.load_matrix()

    # --- Example of how agents could be registered ---
    # class MockExecutiveAgent: pass
    # class MockActionAgent: pass
    # orchestrator.register_agents({
    #     "Executive": MockExecutiveAgent,
    #     "Action": MockActionAgent,
    # })

    # --- Example of routing a valid message ---
    try:
        print("\\n--- Testing a valid route ---")
        orchestrator.route_message(
            from_role="Executive",
            to_role="Action",
            payload={"task": "generate_code", "spec": "Create a new component"}
        )
    except (ValueError, KeyError) as e:
        print(f"Error: {e}")

    # --- Example of routing an invalid message ---
    try:
        print("\\n--- Testing an invalid route ---")
        orchestrator.route_message(
            from_role="Action",
            to_role="Executive",
            payload={"status": "complete"}
        )
    except (ValueError, KeyError) as e:
        print(f"Error: {e}")