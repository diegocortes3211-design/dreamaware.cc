from dataclasses import dataclass

@dataclass
class MoodRisk:
    color: str
    arousal: float # 0..1
    valence: float # 0..1
    risk: float # 0..1 (heuristic)

BASE = {
    "blue": MoodRisk("blue", 0.3, 0.6, 0.35),
    "red": MoodRisk("red", 0.8, 0.4, 0.60),
    "green": MoodRisk("green",0.4, 0.7, 0.30),
    "yellow":MoodRisk("yellow",0.6,0.8, 0.45),
    "purple":MoodRisk("purple",0.5,0.5, 0.50),
}

def score_color(color: str, context_valence: float | None = None) -> MoodRisk:
    m = BASE.get(color.lower())
    if not m:
        return MoodRisk(color, 0.5, 0.5, 0.5)
    if context_valence is not None:
        v = max(0.0, min(1.0, context_valence))
        # simple adjustment: lower valence raises risk slightly
        adj = (0.5 - v) * 0.3
        return MoodRisk(m.color, m.arousal, v, max(0, min(1, m.risk + adj)))
    return m