# tests/test_creativity.py

import unittest
from services.creativity.engine import CreativityEngine
from services.creativity.scorer import CreativityScorer

class TestCreativityEngine(unittest.TestCase):
    """
    Tests for the CreativityEngine.
    """

    def test_generate_variations(self):
        """
        Tests that the engine generates the correct number of variations.
        """
        engine = CreativityEngine()
        base_concept = "agile development"
        variations = engine.generate(base_concept, num_variations=3)
        self.assertEqual(len(variations), 3)
        self.assertIn("agile development through the lens of synergy", variations[0])

    def test_generate_with_empty_concept(self):
        """
        Tests that the engine returns an empty list for an empty base concept.
        """
        engine = CreativityEngine()
        variations = engine.generate("", num_variations=3)
        self.assertEqual(len(variations), 0)


class TestCreativityScorer(unittest.TestCase):
    """
    Tests for the CreativityScorer.
    """

    def test_score_concept(self):
        """
        Tests the basic scoring functionality.
        """
        scorer = CreativityScorer(novelty_factor=0.2)
        concept = "leveraging synergy for paradigm-shifting disruption"
        score = scorer.score(concept)
        self.assertGreater(score, 0.5)
        self.assertLessEqual(score, 1.0)

    def test_score_empty_concept(self):
        """
        Tests that an empty concept receives a score of 0.
        """
        scorer = CreativityScorer()
        score = scorer.score("")
        self.assertEqual(score, 0.0)

    def test_score_clamping(self):
        """
        Tests that the score is properly clamped between 0.0 and 1.0.
        """
        scorer = CreativityScorer(novelty_factor=0.8)
        long_concept = "a very long concept that also happens to contain the buzzwords synergy, disruption, and paradigm through a new lens"
        score = scorer.score(long_concept)
        self.assertEqual(score, 1.0)

if __name__ == "__main__":
    unittest.main()

# commit: test: Add unit tests for Creativity Engine and Scorer.