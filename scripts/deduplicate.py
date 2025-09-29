#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

def canonicalize(text: str) -> str:
    # minimal example: trim, collapse whitespace, lower-case
    return " ".join(text.strip().lower().split())

def content_hash(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode('utf-8'))
    return h.hexdigest()

def dedupe_file(input_fp: Path, output_fp: Path):
    seen = set()
    total, kept, dropped = 0, 0, 0

    with input_fp.open('r', encoding='utf-8') as infile, \
         output_fp.open('w', encoding='utf-8') as outfile:

        for line in infile:
            total += 1
            record = json.loads(line)
            text = record.get('text', '')
            canon = canonicalize(text)
            h = content_hash(canon)

            if h in seen:
                dropped += 1
                continue

            seen.add(h)
            record['content_hash'] = h
            outfile.write(json.dumps(record, ensure_ascii=False) + "\n")
            kept += 1

    print(f"Deduped {input_fp.name}: total={total}, kept={kept}, dropped={dropped}")

def main():
    p = argparse.ArgumentParser(
        description="Remove exact-duplicate records by content hash."
    )
    p.add_argument("--input",  "-i", required=True, type=Path,
                   help="Path to input JSONL with a 'text' field per record")
    p.add_argument("--output", "-o", required=True, type=Path,
                   help="Path to write deduplicated JSONL")
    args = p.parse_args()

    dedupe_file(args.input, args.output)

if __name__ == "__main__":
    main()