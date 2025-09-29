import os, json, psycopg, base64, datetime as dt
from jwcrypto import jwk, jws
from services.audit.merkle import merkle_root
from services.audit.canonical import canonical_row

DB_URL = os.getenv("DB_URL") # read-only or anchoring DB
JWK_ED25519 = os.getenv("ANCHOR_JWK_ED25519_JSON") # {"kty":"OKP","crv":"Ed25519","d":"...","x":"..."}
TREE_VERSION = os.getenv("TREE_VERSION", "v1")

def sign_jws(payload: dict, jwk_json: str) -> str:
    key = jwk.JWK.from_json(jwk_json)
    token = jws.JWS(json.dumps(payload).encode())
    token.add_signature(key, alg="EdDSA", protected=json.dumps({"alg":"EdDSA","typ":"JWT","kid":payload.get("kid","anchor")}))
    return token.serialize(compact=True)

def compute_root(conn) -> tuple[bytes, int]:
    rows = conn.execute("""
        SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;
        SELECT tenant_id, player_id, elo_rating, rank, match_count, updated_at
        FROM leaderboard_entries
        ORDER BY tenant_id, player_id
    """)
    leaves = [canonical_row(dict(r)) for r in rows]
    return merkle_root(leaves), len(leaves)

def get_prev_root(conn) -> bytes | None:
    row = conn.execute("SELECT merkle_root FROM audit_anchor WHERE tree_version=%s ORDER BY seq DESC LIMIT 1", (TREE_VERSION,)).fetchone()
    return None if not row else bytes(row[0])

def main():
    now = dt.datetime.now(dt.timezone.utc)
    with psycopg.connect(DB_URL, autocommit=False) as conn:
        with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
            root, count = compute_root(cur)
            prev = get_prev_root(cur)
            payload = {
                "tv": TREE_VERSION,
                "root": root.hex(),
                "prev_root": prev.hex() if prev else None,
                "snapshot_at": now.isoformat(),
                "node_count": count,
                "kid": "anchor-ed25519-1"
            }
            token = sign_jws(payload, JWK_ED25519)
            cur.execute("""
                INSERT INTO audit_anchor (tree_version, merkle_root, prev_root, node_count, snapshot_at, jws)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING seq
            """, (TREE_VERSION, psycopg.Binary(root), psycopg.Binary(prev) if prev else None, count, now, token))
            seq = cur.fetchone()["seq"]
            # Optional cheap witness (append-only git file)
            witness_dir = os.getenv("ANCHOR_WITNESS_DIR") # e.g., ./anchors/
            if witness_dir:
                os.makedirs(witness_dir, exist_ok=True)
                with open(os.path.join(witness_dir, f"{seq}_{now.date()}.json"), "w") as f:
                    json.dump(payload | {"jws": token}, f, indent=2)
            conn.commit()
            print(json.dumps({"seq": seq, "root": payload["root"], "node_count": count}))

if __name__ == "__main__":
    main()