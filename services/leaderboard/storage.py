# services/leaderboard/storage.py
from typing import Dict, Optional, List
from .models import Entity

class InMemoryStorage:
    """
    An in-memory storage layer for ELO entities.
    This is a simple implementation for demonstration and testing.
    A real-world implementation would use a persistent database.
    """
    def __init__(self):
        self._entities: Dict[str, Entity] = {}

    def add_entity(self, entity: Entity):
        """
        Adds a new entity to the storage.

        Args:
            entity (Entity): The entity to add.

        Raises:
            ValueError: If an entity with the same ID already exists.
        """
        if entity.id in self._entities:
            raise ValueError(f"Entity with ID {entity.id} already exists.")
        self._entities[entity.id] = entity

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """
        Retrieves an entity by its ID.

        Args:
            entity_id (str): The ID of the entity to retrieve.

        Returns:
            Optional[Entity]: The entity if found, otherwise None.
        """
        return self._entities.get(entity_id)

    def update_entity(self, entity: Entity):
        """
        Updates an existing entity in storage.

        Args:
            entity (Entity): The entity with updated information.

        Raises:
            ValueError: If the entity does not exist in storage.
        """
        if entity.id not in self._entities:
            raise ValueError(f"Entity with ID {entity.id} not found.")
        self._entities[entity.id] = entity

    def list_entities(self) -> List[Entity]:
        """
        Returns a list of all entities, sorted by ELO rating in descending order.

        Returns:
            List[Entity]: The sorted list of all entities.
        """
        return sorted(self._entities.values(), key=lambda e: e.elo_rating, reverse=True)

# commit: feat: Implement in-memory storage layer for leaderboard entities.