#!/usr/bin/env python3
import argparse, json, hashlib, base64, pathlib, sys

def verify_witnesses(root_path: pathlib.Path, sigs_dir: pathlib.Path, tuf_meta: pathlib.Path)->bool:
    meta = json.loads(tuf_meta.read_text())
    keys = {k["id"]: base64.b64decode(k["pubkey"]) for k in meta["witness_keys"]}
    want = int(meta.get("threshold", 2))
    ok = 0
    root = root_path.read_bytes()
    for sid, pub in keys.items():
        sigp = sigs_dir / f"{sid}.sig"
        if not sigp.exists():
            continue
        try:
            import nacl.signing
            vk = nacl.signing.VerifyKey(pub)
            sig_bytes = base64.b64decode(sigp.read_text().strip()) if sigp.suffix == ".b64" else sigp.read_bytes()
            vk.verify(root, sig_bytes)
            ok += 1
        except Exception:
            pass
    return ok >= want

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--rekor-record", required=True)
    ap.add_argument("--tuf-metadata", required=True)
    ap.add_argument("--sigs-dir", required=True)
    args = ap.parse_args()

    checkpoint = pathlib.Path(args.checkpoint)
    rekor = pathlib.Path(args.rekor_record)
    tuf = pathlib.Path(args.tuf_metadata)
    sigs = pathlib.Path(args.sigs_dir)

    root_hex = checkpoint.read_text().strip()
    if not all(c in "0123456789abcdef" for c in root_hex.lower()):
        print("ERROR: checkpoint is not hex"); sys.exit(2)

    # Check it's not the sha256 of its own file content (anti-footgun)
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest() == root_hex:
        print("ERROR: checkpoint file must contain raw root hex, not sha256(file)"); sys.exit(2)

    # Rekor record contains root hex (offline loose check)
    if root_hex not in rekor.read_text():
        print("ERROR: Rekor entry does not contain checkpoint root"); sys.exit(2)

    # Witness threshold
    if not verify_witnesses(checkpoint, sigs, tuf):
        print("ERROR: witness threshold not met"); sys.exit(2)

    print("OK: checkpoint anchored and cosigned (threshold met)")

if __name__ == "__main__":
    main()