import math

def token_cost(tokens: int, unit_cost: float = 1e-4) -> float:
    return tokens * unit_cost

def entropy(words: list[str]) -> float:
    # naive unigram entropy (bits)
    if not words:
        return 0.0
    from collections import Counter
    N = len(words); c = Counter(words)
    return -sum((n/N)*math.log2(n/N) for n in c.values())

def creativity_score(text: str) -> float:
    words = text.split()
    H = entropy(words)
    cost = token_cost(len(words))
    return 0.0 if cost == 0 else H / cost