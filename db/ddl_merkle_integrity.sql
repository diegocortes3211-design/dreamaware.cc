-- Canonical anchors for leaderboard state
CREATE TABLE audit_anchor (
    seq BIGSERIAL PRIMARY KEY,
    tree_version TEXT NOT NULL DEFAULT 'v1',
    merkle_root BYTEA NOT NULL, -- 32B SHA-256
    prev_root BYTEA, -- 32B; must match prior seq
    node_count BIGINT NOT NULL,
    snapshot_at TIMESTAMPTZ NOT NULL, -- DB clock
    jws TEXT NOT NULL, -- compact JWS (alg=EdDSA or ES256)
    tsa_stamp BYTEA, -- optional RFC3161 token
    external_ref TEXT, -- e.g., git commit/URL to transparency log
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tree_version, merkle_root)
);

CREATE TABLE audit_anchor_witness (
    anchor_seq BIGINT PRIMARY KEY REFERENCES audit_anchor(seq) ON DELETE CASCADE,
    witness_kind TEXT NOT NULL, -- 'git', 'notary', 'tsl', etc.
    ref TEXT NOT NULL, -- e.g., git sha, notarization receipt
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Fast lookups and chain walking
CREATE INDEX ON audit_anchor (created_at DESC);
CREATE INDEX ON audit_anchor (snapshot_at DESC);

-- Optional guard: reject non-linear chains
CREATE OR REPLACE FUNCTION audit_anchor_guard()
RETURNS trigger AS $$
DECLARE
    prev BYTEA;
BEGIN
    IF NEW.seq > 1 THEN
        SELECT merkle_root INTO prev FROM audit_anchor WHERE seq = NEW.seq - 1;
        IF NEW.prev_root IS DISTINCT FROM prev THEN
            RAISE EXCEPTION 'prev_root mismatch: expected % got %', prev, NEW.prev_root;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_anchor_guard_tr
BEFORE INSERT ON audit_anchor
FOR EACH ROW EXECUTE FUNCTION audit_anchor_guard();