# tests/test_leaderboard.py

import unittest
from services.leaderboard.models import Entity
from services.leaderboard.storage import InMemoryStorage
from services.leaderboard.elo_engine import EloEngine
from services.leaderboard.leaderboard import Leaderboard

class TestLeaderboardIntegration(unittest.TestCase):
    """
    Integration tests for the Leaderboard service.
    """

    def setUp(self):
        """
        Set up a fresh Leaderboard instance for each test.
        """
        storage = InMemoryStorage()
        elo_engine = EloEngine(k_factor=32)
        self.leaderboard = Leaderboard(storage, elo_engine)

        # Add some initial entities for testing with closer ratings
        # to make rank changes more likely in tests.
        self.leaderboard.add_entity("player1", "Alice", 1510)
        self.leaderboard.add_entity("player2", "Bob", 1500)

    def test_add_and_get_entity(self):
        """
        Tests that a new entity can be added and then retrieved.
        """
        self.leaderboard.add_entity("player3", "Charlie", 1550)
        entity = self.leaderboard.get_entity("player3")
        self.assertIsNotNone(entity)
        self.assertEqual(entity.name, "Charlie")
        self.assertEqual(entity.elo_rating, 1550)

    def test_record_match_win_loss(self):
        """
        Tests that recording a match correctly updates ELO ratings for a win/loss.
        """
        # Alice (1600) wins against Bob (1500)
        self.leaderboard.record_match("player1", "player2", 1.0)

        alice = self.leaderboard.get_entity("player1")
        bob = self.leaderboard.get_entity("player2")

        # Alice's rating should increase, Bob's should decrease
        self.assertGreater(alice.elo_rating, 1510)
        self.assertLess(bob.elo_rating, 1500)

    def test_record_match_draw(self):
        """
        Tests that recording a draw correctly updates ELO ratings.
        """
        # Alice (1600) draws with Bob (1500)
        self.leaderboard.record_match("player1", "player2", 0.5)

        alice = self.leaderboard.get_entity("player1")
        bob = self.leaderboard.get_entity("player2")

        # The higher-rated player (Alice) should lose points in a draw with a lower-rated player
        self.assertLess(alice.elo_rating, 1600)
        # The lower-rated player (Bob) should gain points
        self.assertGreater(bob.elo_rating, 1500)

    def test_get_leaderboard_sorting(self):
        """
        Tests that the leaderboard is correctly sorted by ELO rating.
        """
        # Bob (1500) wins against Alice (1600) - an upset
        self.leaderboard.record_match("player2", "player1", 1.0)

        leaderboard = self.leaderboard.get_leaderboard()

        # Bob's rating should now be higher than Alice's
        self.assertGreater(leaderboard[0].elo_rating, leaderboard[1].elo_rating)
        self.assertEqual(leaderboard[0].id, "player2") # Bob should be first

    def test_record_match_with_nonexistent_entity(self):
        """
        Tests that recording a match with a non-existent entity raises a ValueError.
        """
        with self.assertRaises(ValueError):
            self.leaderboard.record_match("player1", "nonexistent", 1.0)

if __name__ == "__main__":
    unittest.main()

# commit: test: Add integration tests for Leaderboard service.