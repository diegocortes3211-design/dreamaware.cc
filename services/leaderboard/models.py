# services/leaderboard/models.py
from dataclasses import dataclass

@dataclass
class Entity:
    """
    Represents a competitor in the ELO system.
    """
    id: str
    name: str
    elo_rating: float = 1500.0  # Default ELO rating for new entities

# commit: feat: Define Entity model for the leaderboard.