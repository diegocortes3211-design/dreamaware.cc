from __future__ import annotations
import re

_EMOJI = re.compile(r"[\U0001F300-\U0001FAFF]")

def strip_slop(text: str) -> str:
    if not text:
        return text
    t = text
    t = _EMOJI.sub("", t)
    t = t.replace("\u2013", "-") # en dash
    t = t.replace("\u2014", "-") # em dash
    t = t.replace("\u00A0", " ") # nbsp
    return t