from .constants import DEFAULT_LESSON_PATTERN

def outline_steps(features: dict) -> list[str]:
    """
    Generates a lesson step sequence based on a default pattern and optional insertions.

    Args:
        features: A dictionary of features about the lesson content, e.g.,
                  {"has_media": True, "claims_count": 3}

    Returns:
        A list of strings representing the sequence of lesson steps.
    """
    steps = DEFAULT_LESSON_PATTERN.copy()

    # Optional inserts that never change first/last positions
    inserts = []
    if features.get("has_media"):                 # audio/video present
        inserts.append(("spot", 1))               # after first read
    if features.get("claims_count", 0) >= 2:      # many factual claims
        inserts.append(("check", len(steps) - 1)) # before reflect

    # Insert steps in reverse index order to avoid shifting indices
    for kind, idx in sorted(inserts, key=lambda x: x[1], reverse=True):
        steps.insert(idx, kind)
    return steps