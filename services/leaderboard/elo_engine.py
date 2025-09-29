# services/leaderboard/elo_engine.py
import math
from typing import Tuple

class EloEngine:
    """
    Computes and updates ELO ratings for two competing entities.
    """
    def __init__(self, k_factor: int = 32):
        """
        Initializes the engine with a specific K-factor.
        Args:
            k_factor (int): The maximum rating adjustment per event.
        """
        self.k = k_factor

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculates the expected score for entity A against entity B.
        """
        return 1 / (1 + math.pow(10, (rating_b - rating_a) / 400))

    def update(self, rating_a: float, rating_b: float, score_a: float) -> Tuple[float, float]:
        """
        Updates the ratings for A and B based on the event's outcome.

        Args:
            rating_a (float): Current rating of entity A.
            rating_b (float): Current rating of entity B.
            score_a (float): The actual score for A (1.0 for win, 0.5 for draw, 0.0 for loss).

        Returns:
            A tuple containing the new ratings for A and B.
        """
        exp_a = self.expected_score(rating_a, rating_b)
        # The score for B is the inverse of A's score
        score_b = 1 - score_a
        exp_b = 1 - exp_a

        new_a = rating_a + self.k * (score_a - exp_a)
        new_b = rating_b + self.k * (score_b - exp_b)

        return round(new_a, 2), round(new_b, 2)

# commit: feat: Implement core EloEngine for rating calculations.