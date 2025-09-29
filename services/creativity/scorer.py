# services/creativity/scorer.py

class CreativityScorer:
    """
    Scores the creativity of a concept based on simple heuristics.
    This is a placeholder for a more advanced scoring model.
    """

    def __init__(self, novelty_factor: float = 0.5):
        """
        Initializes the scorer with a novelty factor.

        Args:
            novelty_factor (float): A weight to apply to the novelty of a concept.
        """
        self.novelty_factor = novelty_factor

    def score(self, concept: str) -> float:
        """
        Scores a concept based on its length and the presence of "buzzwords".

        Args:
            concept (str): The concept to score.

        Returns:
            float: A creativity score between 0.0 and 1.0.
        """
        if not concept:
            return 0.0

        # Simple scoring logic: longer concepts with buzzwords are more "creative"
        score = len(concept) / 100.0  # Normalize by an arbitrary length
        buzzwords = ["synergy", "disruption", "paradigm", "lens"]

        for word in buzzwords:
            if word in concept.lower():
                score += self.novelty_factor

        # Clamp the score to be between 0.0 and 1.0
        return max(0.0, min(1.0, score))

# commit: feat: Add Creativity Scorer module.