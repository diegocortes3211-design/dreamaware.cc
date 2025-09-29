import json, datetime as dt

def canonical_row(row) -> bytes:
    """ Row -> canonical JSON bytes (sorted keys, no whitespace).
    Expect row: (tenant_id, player_id, elo_rating, rank, match_count, updated_at)
    """
    obj = {
        "tenant": str(row["tenant_id"]),
        "player": str(row["player_id"]),
        "elo": int(row["elo_rating"]),
        "rank": int(row["rank"]),
        "matches": int(row["match_count"]),
        "updated_at": row["updated_at"].replace(microsecond=0, tzinfo=dt.timezone.utc).isoformat()
    }
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()