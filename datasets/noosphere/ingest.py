#!/usr/bin/env python3
# datasets/noosphere/ingest.py
from __future__ import annotations
import argparse, hashlib, json, os, sys, time
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import yaml
import requests

# Optional: S3 support (graceful if missing)
try:
    import boto3  # noqa: F401
    HAS_BOTO3 = True
except Exception:
    HAS_BOTO3 = False

# Optional: JSON Schema validation (hook up later when manifest_schema.json is ready)
try:
    from jsonschema import validate  # noqa: F401
    HAS_JSONSCHEMA = True
except Exception:
    HAS_JSONSCHEMA = False


# ---------- Helpers
def sha256_file(fp: Path, bufsize: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with fp.open("rb") as f:
        for chunk in iter(lambda: f.read(bufsize), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text())


def git_rev_or_unknown(repo_root: Path) -> str:
    head = repo_root / ".git" / "HEAD"
    try:
        if head.exists():
            ref = head.read_text().strip()
            if ref.startswith("ref:"):
                ref_path = repo_root / ".git" / ref.split(" ", 1)[1]
                return ref_path.read_text().strip()
            return ref
    except Exception:
        pass
    return "unknown"


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def is_s3_uri(uri: str) -> bool:
    return uri.startswith("s3://")


def is_http_uri(uri: str) -> bool:
    return uri.startswith("http://") or uri.startswith("https://")


# ---------- Config schema (lightweight)
@dataclass
class SourceSpec:
    source_name: str
    source_uri: str
    license: Optional[str] = None
    format: Optional[str] = None
    language: Optional[str] = None
    expected_sha256: Optional[str] = None
    notes: Optional[str] = None
    # Optional override of target filename
    target_name: Optional[str] = None


@dataclass
class NoosphereConfig:
    corpus_name: str
    out_dir: Path
    sources: List[SourceSpec]
    normalization_rules_path: Optional[Path] = None


def load_config(path: Path) -> NoosphereConfig:
    cfg = read_yaml(path)
    out_dir = Path(cfg.get("out_dir", "data/noosphere/raw")).resolve()
    sources: List[SourceSpec] = []
    for s in cfg["sources"]:
        sources.append(SourceSpec(
            source_name=s["source_name"],
            source_uri=s["source_uri"],
            license=s.get("license"),
            format=s.get("format"),
            language=s.get("language"),
            expected_sha256=s.get("expected_sha256"),
            notes=s.get("notes"),
            target_name=s.get("target_name"),
        ))

    normalization_rules_path = Path(cfg["normalization"]["rules"]).resolve() \
        if cfg.get("normalization", {}).get("rules") else None

    return NoosphereConfig(
        corpus_name=cfg["corpus_name"],
        out_dir=out_dir,
        sources=sources,
        normalization_rules_path=normalization_rules_path
    )


# ---------- Fetchers
def fetch_http(uri: str, dest: Path) -> None:
    with requests.get(uri, stream=True, timeout=60) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)


def fetch_s3(uri: str, dest: Path) -> None:
    if not HAS_BOTO3:
        raise RuntimeError("boto3 not installed; cannot fetch s3 URIs")
    # s3://bucket/key...
    _, _, bucket_and_key = uri.partition("s3://")
    bucket, _, key = bucket_and_key.partition("/")
    import boto3
    s3 = boto3.client("s3")
    s3.download_file(bucket, key, str(dest))


def resolve_and_fetch(src: SourceSpec, raw_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    """
    Returns a manifest-ready dict for this source (without normalization info).
    Will skip download if file exists and checksum matches expected (if provided).
    """
    ensure_dir(raw_dir)
    # Choose target filename
    target_name = src.target_name or Path(src.source_uri).name
    local_fp = raw_dir / target_name

    # Download if needed
    downloaded = False
    if local_fp.exists():
        # If we have an expected checksum, verify; else trust existing file
        if src.expected_sha256:
            existing = sha256_file(local_fp)
            if existing.lower() != src.expected_sha256.lower():
                if dry_run:
                    raise RuntimeError(f"[dry-run] checksum mismatch for {local_fp}")
                # re-download
                local_fp.unlink(missing_ok=True)
            else:
                # already good
                pass
    # else: no expected, just keep it

    if not local_fp.exists():
        if dry_run:
            # Simulate download path
            pass
        else:
            if is_http_uri(src.source_uri):
                fetch_http(src.source_uri, local_fp)
            elif is_s3_uri(src.source_uri):
                fetch_s3(src.source_uri, local_fp)
            else:
                # Treat as local file path (copy)
                src_path = Path(src.source_uri).expanduser().resolve()
                if not src_path.exists():
                    raise FileNotFoundError(f"Local source not found: {src_path}")
                local_fp.write_bytes(src_path.read_bytes())
        downloaded = True

    # Compute checksum (even if dry-run, we try to avoid touching filesystem)
    file_sha = sha256_file(local_fp) if local_fp.exists() else None
    file_size = local_fp.stat().st_size if local_fp.exists() else None

    return {
        "source_name": src.source_name,
        "source_uri": src.source_uri,
        "download_date": now_utc_iso(),
        "file_name": local_fp.name,
        "filesize_bytes": file_size,
        "file_sha256": file_sha,
        "license": src.license,
        "format": src.format,
        "language": src.language,
        "notes": src.notes,
        "downloaded": downloaded,
        "local_path": str(local_fp),
    }


# ---------- Normalization rules hashing
def load_and_hash_normalization(rules_path: Optional[Path]) -> Dict[str, Any]:
    """
    Loads the normalization rules file (yaml/json), returns its content and SHA-256.
    Also computes a repo code hash for provenance.
    """
    if not rules_path:
        return {"rules": None, "config_hash": None, "code_version": git_rev_or_unknown(Path(__file__).resolve().parents[2])}

    text = rules_path.read_text()
    try:
        rules = yaml.safe_load(text) if rules_path.suffix in {".yml", ".yaml"} else json.loads(text)
    except Exception:
        # If it’s not valid YAML/JSON, keep it as raw text blob
        rules = {"raw_text": text}

    conf_hash = sha256_bytes(text.encode("utf-8"))
    repo_root = Path(__file__).resolve().parents[2]  # project root (adjust if needed)
    return {
        "rules": rules,
        "config_hash": conf_hash,
        "code_version": git_rev_or_unknown(repo_root),
    }


# ---------- Manifest writer
def write_manifest(manifest: Dict[str, Any], out_fp: Path, schema_fp: Optional[Path] = None) -> None:
    if schema_fp and HAS_JSONSCHEMA and schema_fp.exists():
        from jsonschema import validate
        schema = json.loads(schema_fp.read_text())
        validate(manifest, schema)  # raise on error
    out_fp.write_text(json.dumps(manifest, indent=2, sort_keys=True))


# ---------- CLI
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Noosphere snapshot ingestion")
    p.add_argument("--config", required=True, type=Path,
                   help="Path to datasets/noosphere/config.yaml")
    p.add_argument("--out", type=Path,
                   help="Override output base dir (raw, normalized, manifests)")
    p.add_argument("--dry-run", action="store_true",
                   help="Do not download; only resolve and stage manifest")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)

    # Folders
    base_out = (args.out or cfg.out_dir).resolve()
    raw_dir = base_out / "raw"
    norm_dir = base_out / "normalized"
    man_dir = base_out / "manifests"
    ensure_dir(raw_dir); ensure_dir(norm_dir); ensure_dir(man_dir)

    # Run metadata
    run_id = hashlib.sha256(f"{time.time_ns()}-{os.getpid()}".encode()).hexdigest()[:32]
    snapshot_date = now_utc_iso()

    # 1) Resolve & fetch sources
    source_records: List[Dict[str, Any]] = []
    for src in cfg.sources:
        rec = resolve_and_fetch(src, raw_dir, dry_run=args.dry_run)
        source_records.append(rec)

    # 2) Load normalization rule-set & hashes (just metadata here; apply later)
    norm_meta = load_and_hash_normalization(cfg.normalization_rules_path)

    # 3) Build initial manifest (no normalization steps yet—just ingestion proof)
    manifest = {
        "manifest_version": "1.0",
        "snapshot_date": snapshot_date,
        "pipeline_run_id": run_id,
        "corpus_name": cfg.corpus_name,
        "config_hash": norm_meta["config_hash"],
        "code_version": norm_meta["code_version"],
        "sources": [
            {
                k: v for k, v in rec.items()
                if k not in {"local_path", "downloaded"}  # keep manifest portable
            } for rec in source_records
        ],
        "normalization": {
            "steps": [],  # you’ll append concrete steps after you actually normalize
            "rules": norm_meta["rules"],
        },
    }

    # 4) Write manifest (and optionally validate)
    manifest_fp = man_dir / f"{cfg.corpus_name}-{run_id}.manifest.json"
    schema_fp = Path(__file__).resolve().parents[2] / "datasets" / "noosphere" / "manifest_schema.json"
    write_manifest(manifest, manifest_fp, schema_fp if schema_fp.exists() else None)

    print(f"✓ Wrote manifest → {manifest_fp}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)