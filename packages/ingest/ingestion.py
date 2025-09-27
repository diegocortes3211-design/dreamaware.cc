"""Ingestion module: fetch content, preprocess, and hand to retrieval."""
from __future__ import annotations
from pathlib import Path
from typing import List
from .fetch import fetch_url, FetchError, read_file

MAX_FILE_BYTES = 2_000_000

class IngestAgent:
    def __init__(self, retriever, prompt_chain):
        self.retriever = retriever
        self.prompt_chain = prompt_chain

    def fetch_content(self, source: str) -> str:
        """Fetch content. Default path is URL via SSRF-guarded fetcher.

        If source begins with http or https, fetch over the network.
        Otherwise treat as a local file path with size limits.
        """
        s = source.strip()
        if s.lower().startswith(("http://", "https://")):
            return fetch_url(s)

        p = Path(s)
        if not p.exists() or not p.is_file():
            raise FetchError(f"not found: {s}")
        return read_file(p, max_bytes=MAX_FILE_BYTES)

    def preprocess(self, content: str) -> List[str]:
        """Very small, safe default: paragraph chunking with length cap."""
        raw = [seg.strip() for seg in content.split("\n\n") if seg.strip()]
        out: List[str] = []
        buf = ""
        cap = 1200  # characters per chunk
        for seg in raw:
            if len(seg) > cap:
                # crude split on sentence boundaries
                parts = []
                cur = ""
                for tok in seg.split(". "):
                    nxt = (cur + ". " + tok).strip(". ") if cur else tok
                    if len(nxt) > cap:
                        if cur:
                            parts.append(cur)
                        cur = tok
                    else:
                        cur = nxt
                if cur:
                    parts.append(cur)

                for p in parts:
                    if p:
                        out.append(p)
                continue

            if len(buf) + len(seg) + 2 <= cap:
                buf = f"{buf}\n\n{seg}" if buf else seg
            else:
                if buf:
                    out.append(buf)
                buf = seg
        if buf:
            out.append(buf)
        return out

    def store_embeddings(self, chunks: List[str]) -> None:
        """Placeholder. Implement embedding persistence in your vector store."""
        return