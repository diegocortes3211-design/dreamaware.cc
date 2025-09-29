from __future__ import annotations
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel, Field, ValidationError

# Define the path to the configuration file, making it relative to this file's location
# to ensure it can be found regardless of where the script is run from.
CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "syzygy_matrix.yaml"

# Pydantic models for validation
class AgentConfig(BaseModel):
    """Defines the schema for a single agent in the Syzygy Matrix."""
    capabilities: List[str]
    inputs: List[str]
    outputs: List[str]

class DataFlow(BaseModel):
    """
    Defines the schema for a single data flow between agents.
    Aliases are used because 'from' is a reserved keyword in Python.
    """
    from_role: str = Field(..., alias="from")
    to_role: str = Field(..., alias="to")
    data_type: str

class SyzygyMatrix(BaseModel):
    """The root model for the Syzygy Matrix configuration."""
    agents: Dict[str, AgentConfig]
    data_flows: List[DataFlow]


class Orchestrator:
    """
    The Orchestrator is the central nervous system of the agentic architecture.
    It loads the Syzygy Matrix configuration to enforce the rules of engagement
    between different agents, ensuring that all interactions adhere to the
    predefined data flows.
    """
    def __init__(self, config_path: Path = CONFIG_PATH):
        """
        Initializes the Orchestrator with the path to the Syzygy Matrix config.

        Args:
            config_path: The path to the syzygy_matrix.yaml file.
        """
        self.config_path = config_path
        self.matrix: Optional[SyzygyMatrix] = None
        self.agent_map: Dict[str, Type] = {}

    def load_matrix(self) -> SyzygyMatrix:
        """
        Loads and validates the Syzygy Matrix from the YAML configuration file.
        This method is the entry point for initializing the orchestrator's state.

        Returns:
            The validated SyzygyMatrix object.

        Raises:
            ValidationError: If the configuration file does not match the schema.
            FileNotFoundError: If the configuration file cannot be found.
        """
        raw_config = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))
        try:
            self.matrix = SyzygyMatrix(**raw_config)
        except ValidationError as e:
            # Re-raise with a more informative error message.
            raise ValidationError(f"Syzygy Matrix validation failed: {e}") from e
        return self.matrix

    def register_agents(self, agent_classes: Dict[str, Type]) -> None:
        """
        Registers agent classes against the roles defined in the Syzygy Matrix.

        Args:
            agent_classes: A dictionary mapping agent roles to their classes.

        Raises:
            RuntimeError: If the matrix has not been loaded first.
            KeyError: If an agent role is not defined in the Syzygy Matrix.
        """
        if not self.matrix:
            raise RuntimeError("The Syzygy Matrix must be loaded before registering agents.")

        for role in agent_classes:
            if role not in self.matrix.agents:
                raise KeyError(f"Agent role '{role}' is not defined in the Syzygy Matrix.")

        self.agent_map.update(agent_classes)

    def route_message(self, from_role: str, to_role: str, payload: Any) -> None:
        """
        Routes a message between two agents, enforcing the data flow rules.
        In a real system, this would interact with a message queue (e.g., Redis, RabbitMQ).

        Args:
            from_role: The role of the agent sending the message.
            to_role: The role of the agent receiving the message.
            payload: The data being sent.

        Raises:
            RuntimeError: If the matrix has not been loaded first.
            ValueError: If the data flow is not permitted by the Syzygy Matrix.
        """
        if not self.matrix:
            raise RuntimeError("The Syzygy Matrix must be loaded before routing messages.")

        is_permitted = any(
            flow.from_role == from_role and flow.to_role == to_role
            for flow in self.matrix.data_flows
        )

        if not is_permitted:
            raise ValueError(f"Data flow from '{from_role}' to '{to_role}' is not permitted by the Syzygy Matrix.")

        # This is a placeholder for the actual message-passing logic.
        print(f"Message successfully routed from {from_role} to {to_role}.")