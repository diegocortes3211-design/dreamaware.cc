from __future__ import annotations
from pathlib import Path
from typing import List
from urllib.parse import urlsplit
from .fetch import fetch_url, read_file, FetchError

MAX_FILE_BYTES = 2_000_000

class IngestAgent:
    def __init__(self, retriever, prompt_chain):
        self.retriever = retriever
        self.prompt_chain = prompt_chain

    def fetch_content(self, source: str) -> str:
        """ Fetches content from a URL or local file path using hardened fetchers. """
        s = source.strip()
        parts = urlsplit(s)
        if parts.scheme:
            # Only allow http/https
            if parts.scheme.lower() in ("http", "https"):
                return fetch_url(s, max_bytes=MAX_FILE_BYTES)
            raise FetchError(f"unsupported URL scheme: {parts.scheme}")

        p = Path(s)
        if not p.is_file():
            raise FetchError(f"local path not found or not a file: {s}")
        return read_file(p, max_bytes=MAX_FILE_BYTES)

    def preprocess(self, content: str) -> List[str]:
        """ Splits raw content into text chunks for embedding. """
        # Paragraph-first, then sentence pack to ~1200 chars without splitting words.
        cap = 1200
        paras = [seg.strip() for seg in content.split("\n\n") if seg.strip()]
        out: List[str] = []
        buf: str = ""
        def flush():
            nonlocal buf
            if buf:
                out.append(buf)
            buf = ""

        for para in paras:
            if len(para) <= cap:
                if not buf:
                    buf = para
                elif len(buf) + 2 + len(para) <= cap:
                    buf = f"{buf}\n\n{para}"
                else:
                    flush()
                    buf = para
                continue
            # Split long paragraph by sentence-ish boundaries
            sentences = []
            cur = ""
            for tok in para.split(". "):
                nxt = (cur + ". " + tok).strip()
                if len(nxt) > cap:
                    if cur:
                        sentences.append(cur)
                    cur = tok
                else:
                    cur = nxt
            if cur:
                sentences.append(cur)

            for snt in sentences:
                if len(snt) <= cap:
                    if not buf:
                        buf = snt
                    elif len(buf) + 1 + len(snt) <= cap:
                        buf = f"{buf} {snt}"
                    else:
                        flush()
                        buf = snt
                else:
                    # Last resort: hard wrap by characters
                    start = 0
                    while start < len(snt):
                        chunk = snt[start:start+cap]
                        if buf:
                            flush()
                        out.append(chunk)
                        start += cap
        flush()
        return out

    def store_embeddings(self, chunks: List[str]) -> None:
        """Placeholder for embedding and storage logic."""
        pass