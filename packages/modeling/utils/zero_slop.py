import re
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF]")
FANCY_DASH_RE = re.compile(r"[\u2013\u2014]") # en and em
EXTRA_WS_RE = re.compile(r"\s+")
def strip_slop(text: str) -> str:
    t = EMOJI_RE.sub("", text)
    t = FANCY_DASH_RE.sub("-", t)
    t = t.replace("\u00A0", " ") # non-breaking space
    t = EXTRA_WS_RE.sub(" ", t).strip()
    return t