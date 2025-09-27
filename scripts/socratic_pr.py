# Socratic PR script
import re

def slop_score(md: str):
    """
    Prefer project SlopScorer; gracefully fall back to a lightweight heuristic.
    Returns a dict with keys: score, emojis, emdash, endash
    """
    try:
        from services.scorecard.slop_scorer import SlopScorer  # type: ignore
        res = SlopScorer().score(md)
        return {
            "score": float(res.get("score", 0.0)),
            "emojis": int(res.get("emojis", 0)),
            "emdash": int(res.get("emdash", 0)),
            "endash": int(res.get("endash", 0)),
        }
    except ImportError:
        emojis = len(re.findall(r"[\U0001F300-\U0001FAFF]", md))
        emdash = md.count("—")
        endash = md.count("–")
        score = min(1.0, 0.02 * emojis + 0.01 * emdash + 0.01 * endash)
        return {"score": score, "emojis": emojis, "emdash": emdash, "endash": endash}

def main():
    print("Running Socratic PR script...")

if __name__ == "__main__":
    main()