from __future__ import annotations
import io
from pathlib import Path
import requests
from typing import Optional
from services.security.net import verify_url
from urllib.parse import urljoin

class FetchError(RuntimeError):
    pass

def _stream_read(resp, *, max_bytes: int) -> bytes:
    data = bytearray()
    for chunk in resp.iter_content(chunk_size=8192):
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > max_bytes:
            raise FetchError("response too large")
    return bytes(data)

def fetch_url(url: str, *, max_bytes: int = 2_000_000, timeout: int = 15) -> str:
    """
    SSRF guarded fetch with redirect revalidation and hard byte cap.
    Returns UTF-8 text.
    """
    safe = verify_url(url)
    try:
        # Do not follow redirects automatically
        with requests.get(safe, stream=True, timeout=timeout, allow_redirects=False) as r:
            if 300 <= r.status_code < 400 and "Location" in r.headers:
                loc = r.headers["Location"]
                abs_loc = urljoin(safe, loc)  # resolve relative redirects
                safe_redirect = verify_url(abs_loc)
                with requests.get(safe_redirect, stream=True, timeout=timeout, allow_redirects=False) as r2:
                    r2.raise_for_status()
                    # Content-Length precheck if available
                    cl = r2.headers.get("Content-Length")
                    if cl and int(cl) > max_bytes:
                        raise FetchError("response too large")
                    data = _stream_read(r2, max_bytes=max_bytes)
                    return data.decode("utf-8", errors="ignore")
            r.raise_for_status()
            cl = r.headers.get("Content-Length")
            if cl and int(cl) > max_bytes:
                raise FetchError("response too large")
            data = _stream_read(r, max_bytes=max_bytes)
            return data.decode("utf-8", errors="ignore")
    except requests.RequestException as e:
        raise FetchError(str(e)) from e

def read_file(path: Path, *, max_bytes: int = 2_000_000) -> str:
    """Safe local file reader with size cap. Returns UTF-8 text."""
    try:
        b = path.read_bytes()
        if len(b) > max_bytes:
            raise FetchError("file too large")
        return io.BytesIO(b).read().decode("utf-8", errors="ignore")
    except Exception as e:
        raise FetchError(str(e)) from e