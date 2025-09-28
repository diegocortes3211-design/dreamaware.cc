from __future__ import annotations
from typing import List

class SimpleTokenizer:
    # Placeholder tokenizer if transformers is not present
    def encode(self, text: str) -> List[int]:
        return [len(tok) for tok in text.split()]

    def decode(self, ids: List[int]) -> str:
        return " ".join(["x" * i for i in ids])

def get_tokenizer(model_name: str):
    try:
        from transformers import AutoTokenizer # type: ignore
        return AutoTokenizer.from_pretrained(model_name)
    except Exception:
        return SimpleTokenizer()