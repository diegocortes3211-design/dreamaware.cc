from __future__ import annotations

def calculate_trust_score(text: str) -> float:
    """
    Calculates a trust score for a given text.
    Placeholder logic: rewards longer text, penalizes excessive exclamation points.
    """
    length_bonus = min(len(text) / 5000, 0.5)  # Max 0.5 bonus for 5000+ chars
    exclamation_penalty = text.count('!') * 0.05

    base_score = 0.5
    score = base_score + length_bonus - exclamation_penalty

    # Ensure score is within [0, 1]
    return max(0.0, min(1.0, score))

def calculate_ai_slop_score(text: str) -> float:
    """
    Calculates an "AI Slop" score, identifying overly generic or unrefined AI-like text.
    Placeholder logic: penalizes common AI-generated phrases.
    """
    slop_phrases = [
        "in conclusion",
        "it is important to note",
        "as a large language model",
        "delve into",
        "tapestry of",
        "unleash the power",
    ]

    penalty = 0.0
    lower_text = text.lower()
    for phrase in slop_phrases:
        if phrase in lower_text:
            penalty += 0.15

    # Ensure score is within [0, 1]
    return max(0.0, min(1.0, penalty))