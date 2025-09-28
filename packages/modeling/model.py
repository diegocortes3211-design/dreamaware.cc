from __future__ import annotations
from typing import Dict, Any

class EchoModel:
    def __init__(self):
        pass
    def generate(self, prompt: str, max_new_tokens: int = 128) -> str:
        return f"[echo] {prompt[:max_new_tokens]}"
    def save_pretrained(self, path: str) -> None:
        pass

class HFModel:
    def __init__(self, model_name: str):
        from transformers import AutoModelForCausalLM # type: ignore
        from transformers import AutoTokenizer # type: ignore
        self.tok = AutoTokenizer.from_pretrained(model_name)
        self.mdl = AutoModelForCausalLM.from_pretrained(model_name)
    def generate(self, prompt: str, max_new_tokens: int = 128) -> str:
        import torch # type: ignore
        ids = self.tok(prompt, return_tensors="pt").input_ids
        out = self.mdl.generate(ids, max_new_tokens=max_new_tokens)
        return self.tok.decode(out[0], skip_special_tokens=True)
    def save_pretrained(self, path: str) -> None:
        self.mdl.save_pretrained(path)

def get_model(cfg: Dict[str, Any]):
    name = cfg.get("model_name", "")
    try:
        if name:
            return HFModel(name)
        raise RuntimeError("no model name")
    except Exception:
        return EchoModel()