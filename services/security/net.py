from __future__ import annotations
import ipaddress
import socket
from typing import List
from urllib.parse import urlparse, urlunparse
import yaml
from pathlib import Path

class SSRFBlocked(ValueError):
    pass

_ROOT = Path(__file__).resolve().parents[2]
_ALLOWLIST_CFG = _ROOT / "configs" / "url_allowlist.yaml"
_ALLOWED_DOMAINS: List[str] = []
_DEFAULT_ALLOWED_PORTS = {80, 443}

_BLOCKED_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),       # RFC1918
    ipaddress.ip_network("172.16.0.0/12"),    # RFC1918
    ipaddress.ip_network("192.168.0.0/16"),   # RFC1918
    ipaddress.ip_network("169.254.0.0/16"),   # link local
    ipaddress.ip_network("::1/128"),          # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),         # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),        # IPv6 link local
    ipaddress.ip_network("ff00::/8"),         # IPv6 multicast
]

def _load_allowlist() -> List[str]:
    global _ALLOWED_DOMAINS
    if _ALLOWED_DOMAINS:
        return _ALLOWED_DOMAINS
    if _ALLOWLIST_CFG.exists():
        data = yaml.safe_load(_ALLOWLIST_CFG.read_text(encoding="utf-8")) or {}
        _ALLOWED_DOMAINS = [d.strip().lower() for d in data.get("allowed_domains", []) if d]
    return _ALLOWED_DOMAINS

def _host_in_allowlist(host: str, allowlist: List[str]) -> bool:
    host_l = host.lower()
    for d in allowlist:
        if host_l == d or host_l.endswith("." + d):
            return True
    return False

def _is_blocked_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    if addr.is_multicast or addr.is_unspecified or addr.is_reserved:
        return True
    for net in _BLOCKED_NETS:
        if addr in net:
            return True
    return False

def _idna(host: str) -> str:
    try:
        return host.encode("idna").decode("ascii")
    except Exception:
        return host

def verify_url(url: str) -> str:
    """
    Verify scheme, allowlist, and resolved IPs for both IPv4 and IPv6.
    Returns a normalized URL on success, raises SSRFBlocked on any violation.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFBlocked(f"invalid scheme: {parsed.scheme}")
    if not parsed.hostname:
        raise SSRFBlocked("missing hostname")
    if parsed.username or parsed.password:
        raise SSRFBlocked("embedded credentials not allowed")

    host_ascii = _idna(parsed.hostname).rstrip(".")
    allowlist = _load_allowlist()
    if not _host_in_allowlist(host_ascii, allowlist):
        raise SSRFBlocked(f"domain not in allowlist: {host_ascii}")

    # basic port policy
    if parsed.port is not None and parsed.port not in _DEFAULT_ALLOWED_PORTS:
        raise SSRFBlocked(f"port not allowed: {parsed.port}")

    # If hostname is a literal IP, validate it directly
    try:
        ipaddress.ip_address(host_ascii)
        literal_ip = True
    except ValueError:
        literal_ip = False

    if literal_ip:
        if _is_blocked_ip(host_ascii):
            raise SSRFBlocked(f"blocked literal IP: {host_ascii}")
    else:
        # Resolve all addresses and block on any private or restricted result
        try:
            infos = socket.getaddrinfo(host_ascii, None, proto=socket.IPPROTO_TCP)
        except socket.gaierror as e:
            raise SSRFBlocked(f"DNS error: {e}") from e

        for _family, _stype, _proto, _canon, sockaddr in infos:
            ip = sockaddr[0]
            if _is_blocked_ip(ip):
                raise SSRFBlocked(f"blocked resolved IP: {ip}")

    # Normalize to ascii host
    netloc = host_ascii
    if parsed.port:
        netloc = f"{host_ascii}:{parsed.port}"
    normalized = parsed._replace(netloc=netloc)
    return urlunparse(normalized)