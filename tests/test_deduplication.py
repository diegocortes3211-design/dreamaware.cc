import json
from pathlib import Path
from scripts.deduplicate import dedupe_file

def test_dedupe_file(tmp_path: Path):
    # 1. Create a dummy input file with duplicate records
    input_content = [
        {"id": 1, "text": "alpha bravo charlie"},
        {"id": 2, "text": "delta echo foxtrot"},
        {"id": 3, "text": "alpha bravo charlie"},  # Duplicate
        {"id": 4, "text": "golf hotel india"},
        {"id": 5, "text": "delta echo foxtrot"}, # Duplicate
    ]
    input_file = tmp_path / "input.jsonl"
    with input_file.open("w", encoding="utf-8") as f:
        for record in input_content:
            f.write(json.dumps(record) + "\n")

    # 2. Define the output file path
    output_file = tmp_path / "output.jsonl"

    # 3. Run the deduplication function
    dedupe_file(input_file, output_file)

    # 4. Verify the output
    assert output_file.exists()

    output_records = []
    with output_file.open("r", encoding="utf-8") as f:
        for line in f:
            output_records.append(json.loads(line))

    # Check that duplicates are removed (3 unique records should remain)
    assert len(output_records) == 3

    # Check that the correct records were kept
    kept_ids = {record["id"] for record in output_records}
    assert kept_ids == {1, 2, 4}

    # Check that each record has a content_hash
    for record in output_records:
        assert "content_hash" in record
        assert isinstance(record["content_hash"], str)
        assert len(record["content_hash"]) == 64  # SHA-256 hex digest length