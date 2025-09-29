# services/leaderboard/leaderboard.py
from typing import List, Optional

from .models import Entity
from .storage import InMemoryStorage
from .elo_engine import EloEngine

class Leaderboard:
    """
    Manages the ELO leaderboard, including entities and match results.
    """
    def __init__(self, storage: InMemoryStorage, elo_engine: EloEngine):
        """
        Initializes the Leaderboard with storage and an ELO engine.

        Args:
            storage (InMemoryStorage): The storage layer for entities.
            elo_engine (EloEngine): The engine for calculating ELO ratings.
        """
        self.storage = storage
        self.elo_engine = elo_engine

    def add_entity(self, entity_id: str, name: str, initial_rating: float = 1500.0):
        """
        Creates and adds a new entity to the leaderboard.

        Args:
            entity_id (str): The unique ID for the new entity.
            name (str): The name of the new entity.
            initial_rating (float): The starting ELO rating.
        """
        entity = Entity(id=entity_id, name=name, elo_rating=initial_rating)
        self.storage.add_entity(entity)

    def record_match(self, entity_a_id: str, entity_b_id: str, score_a: float):
        """
        Records a match result and updates the ratings of the two entities.

        Args:
            entity_a_id (str): The ID of the first entity.
            entity_b_id (str): The ID of the second entity.
            score_a (float): The score for entity A (1.0 for win, 0.5 for draw, 0.0 for loss).

        Raises:
            ValueError: If either entity is not found.
        """
        entity_a = self.storage.get_entity(entity_a_id)
        entity_b = self.storage.get_entity(entity_b_id)

        if not entity_a or not entity_b:
            raise ValueError("One or both entities not found.")

        new_rating_a, new_rating_b = self.elo_engine.update(
            entity_a.elo_rating, entity_b.elo_rating, score_a
        )

        entity_a.elo_rating = new_rating_a
        entity_b.elo_rating = new_rating_b

        self.storage.update_entity(entity_a)
        self.storage.update_entity(entity_b)

    def get_leaderboard(self) -> List[Entity]:
        """
        Retrieves the current leaderboard, sorted by ELO rating.

        Returns:
            List[Entity]: A sorted list of all entities.
        """
        return self.storage.list_entities()

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Retrieves a single entity by its ID.

        Args:
            entity_id (str): The ID of the entity.

        Returns:
            Optional[Entity]: The entity if found, otherwise None.
        """
        return self.storage.get_entity(entity_id)

# commit: feat: Implement Leaderboard service to orchestrate ELO interactions.