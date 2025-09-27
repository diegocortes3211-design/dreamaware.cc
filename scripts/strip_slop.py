#!/usr/bin/env python3
import sys, re, pathlib

def clean(s: str) -> str:
    s = re.sub(r"[\u2000-\u200B\u00A0]", " ", s)  # thin spaces, NBSP
    s = s.replace("—", "-").replace("–", "-")     # normalize dashes
    s = re.sub(r"[\U0001F300-\U0001FAFF]", "", s) # remove emojis
    return s

for path in sys.argv[1:]:
    p = pathlib.Path(path)
    if not p.is_file():
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
        c = clean(t)
        if c != t:
            p.write_text(c, encoding="utf-8")
    except Exception:
        continue