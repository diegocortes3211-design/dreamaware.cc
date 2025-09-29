# services/psychology/impactevaluator.py

class ImpactEvaluator:
    """
    Evaluates the potential psychological impact of a text based on the
    frameworks it maps to.
    """

    def __init__(self):
        """
        Initializes the evaluator with a predefined set of impact scores
        for each psychological framework.
        """
        self.impact_scores = {
            "Cognitive Behavioral Therapy (CBT)": 0.6,
            "Maslow's Hierarchy of Needs": 0.4,
            "Big Five Personality Traits": 0.3,
            "Psychoanalytic Theory": 0.8  # Higher impact due to depth
        }

    def evaluate_impact(self, frameworks: list) -> float:
        """
        Calculates a total impact score based on a list of detected frameworks.

        The final score is the sum of the individual framework scores, clamped
        at a maximum of 1.0.

        Args:
            frameworks (list): A list of psychological framework names.

        Returns:
            float: A total impact score between 0.0 and 1.0.
        """
        if not frameworks:
            return 0.0

        total_score = 0.0
        for framework in frameworks:
            total_score += self.impact_scores.get(framework, 0.0)

        # Clamp the score at 1.0
        return min(1.0, total_score)

# commit: feat: Add Impact Evaluator for psychological frameworks.