# tests/test_psychology.py

import unittest
from services.psychology.framework_mapper import PsychologyFrameworkMapper
from services.psychology.impactevaluator import ImpactEvaluator

class TestPsychologyFrameworkMapper(unittest.TestCase):
    """
    Tests for the PsychologyFrameworkMapper.
    """

    def setUp(self):
        self.mapper = PsychologyFrameworkMapper()

    def test_map_text_to_cbt(self):
        """
        Tests that text with CBT keywords is mapped correctly.
        """
        text = "This thought pattern is affecting my behavior."
        frameworks = self.mapper.map_text_to_frameworks(text)
        self.assertIn("Cognitive Behavioral Therapy (CBT)", frameworks)

    def test_map_text_to_multiple_frameworks(self):
        """
        Tests that text can be mapped to multiple frameworks.
        """
        text = "My childhood experiences affect my unconscious need for safety."
        frameworks = self.mapper.map_text_to_frameworks(text)
        self.assertIn("Psychoanalytic Theory", frameworks)
        self.assertIn("Maslow's Hierarchy of Needs", frameworks)
        self.assertEqual(len(frameworks), 2)

    def test_map_empty_text(self):
        """
        Tests that empty text results in no mapped frameworks.
        """
        frameworks = self.mapper.map_text_to_frameworks("")
        self.assertEqual(len(frameworks), 0)

    def test_map_text_with_no_keywords(self):
        """
        Tests that text without any keywords maps to no frameworks.
        """
        text = "This is a neutral sentence about the weather."
        frameworks = self.mapper.map_text_to_frameworks(text)
        self.assertEqual(len(frameworks), 0)


class TestImpactEvaluator(unittest.TestCase):
    """
    Tests for the ImpactEvaluator.
    """

    def setUp(self):
        self.evaluator = ImpactEvaluator()

    def test_evaluate_single_framework(self):
        """
        Tests the impact evaluation for a single framework.
        """
        frameworks = ["Cognitive Behavioral Therapy (CBT)"]
        score = self.evaluator.evaluate_impact(frameworks)
        self.assertEqual(score, 0.6)

    def test_evaluate_multiple_frameworks(self):
        """
        Tests the impact evaluation for multiple frameworks.
        """
        frameworks = ["Psychoanalytic Theory", "Maslow's Hierarchy of Needs"]
        score = self.evaluator.evaluate_impact(frameworks)
        # 0.8 (Psychoanalytic) + 0.4 (Maslow) = 1.2, which should be clamped to 1.0
        self.assertEqual(score, 1.0)

    def test_evaluate_with_unknown_framework(self):
        """
        Tests that an unknown framework contributes 0 to the score.
        """
        frameworks = ["A Fake Framework", "Big Five Personality Traits"]
        score = self.evaluator.evaluate_impact(frameworks)
        self.assertEqual(score, 0.3)

    def test_evaluate_with_empty_list(self):
        """
        Tests that an empty list of frameworks results in a score of 0.
        """
        score = self.evaluator.evaluate_impact([])
        self.assertEqual(score, 0.0)

if __name__ == "__main__":
    unittest.main()

# commit: test: Add unit tests for Psychology Framework Mapper and Impact Evaluator.