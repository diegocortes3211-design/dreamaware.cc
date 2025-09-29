import os, json, sys, psycopg, datetime as dt
from jwcrypto import jwk, jws
from services.audit.merkle import merkle_root
from services.audit.canonical import canonical_row

DB_URL = os.getenv("DB_URL")
PUB_JWK = os.getenv("ANCHOR_PUB_JWK_JSON") # public Ed25519 JWK
TREE_VERSION = os.getenv("TREE_VERSION", "v1")
DAYS = int(os.getenv("VERIFY_DAYS", "7"))

def verify_jws(compact: str, jwk_json: str) -> dict:
    key = jwk.JWK.from_json(jwk_json)
    t = jws.JWS()
    t.deserialize(compact)
    t.verify(key)
    return json.loads(t.payload)

def recompute(conn, snapshot_at) -> str:
    rows = conn.execute("""
        SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
        SELECT tenant_id, player_id, elo_rating, rank, match_count, updated_at
        FROM leaderboard_entries
        WHERE updated_at <= %s
        ORDER BY tenant_id, player_id
    """, (snapshot_at,))
    leaves = [canonical_row(dict(r)) for r in rows]
    return merkle_root(leaves).hex()

def main():
    start = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=DAYS)
    results = []
    ok = True
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        cur = conn.cursor(row_factory=psycopg.rows.dict_row)
        cur.execute("""
            SELECT seq, merkle_root, prev_root, snapshot_at, jws
            FROM audit_anchor
            WHERE tree_version=%s AND snapshot_at >= %s
            ORDER BY seq ASC
        """, (TREE_VERSION, start))
        anchors = cur.fetchall()
        # Chain check & recompute
        last = None
        for a in anchors:
            payload = verify_jws(a["jws"], PUB_JWK)
            expected_prev = last.hex() if last else None
            chain_ok = (payload["prev_root"] == expected_prev)
            recomputed = recompute(cur, a["snapshot_at"])
            root_db = bytes(a["merkle_root"]).hex()
            state_ok = (recomputed == root_db == payload["root"])
            res = {
                "seq": a["seq"],
                "chain_ok": chain_ok,
                "state_ok": state_ok,
                "root_anchor": root_db,
                "root_recomputed": recomputed,
                "prev_in_payload": payload["prev_root"],
                "prev_expected": expected_prev
            }
            results.append(res)
            ok = ok and chain_ok and state_ok
            last = bytes(a["merkle_root"])
    os.makedirs("reports", exist_ok=True)
    with open("reports/merkle_integrity_report.json", "w") as f:
        json.dump({"passed": ok, "checked": len(results), "results": results}, f, indent=2)
    print(json.dumps({"passed": ok, "checked": len(results)}))
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()