SHELL := /usr/bin/env bash
.DEFAULT_GOAL := all

# ---------- env ----------
VAULT_ADDR ?= http://127.0.0.1:8200
VAULT_TOKEN ?= root
VAULT_TRANSIT_KEY ?= ledger-ed25519
REKOR_URL ?= https://rekor.sigstore.dev
COSIGN_EXPERIMENTAL ?= 1

export VAULT_ADDR VAULT_TOKEN VAULT_TRANSIT_KEY REKOR_URL COSIGN_EXPERIMENTAL

# ---------- local developer targets (non-canonical) ----------
all: proofs-index

up:
	docker compose up -d --build
	@echo "Cluster + Vault + Ledger started."

down:
	docker compose down -v

append-smoke:
	@curl -sS -XPOST localhost:8088/append \
	 -H 'Content-Type: application/json' \
	 -d '{"subject":"smoke","payload":"aGVsbG8=","meta":{"actor":"runner"}}' | cat

proofs-index:
	@printf "# Fortress v4 — Binder\n\n" > docs/PROOFS_INDEX.md
	@printf -- "- Chaos Report → docs/proofs/CHAOS_REPORT.md\n" >> docs/PROOFS_INDEX.md
	@printf -- "- Anchoring Proof → docs/proofs/anchoring/\n" >> docs/PROOFS_INDEX.md
	@printf -- "- Key Custody Dossier → docs/proofs/custody/\n" >> docs/PROOFS_INDEX.md
	@printf -- "- SnapSec Refactor Evidence → GitHub Artifacts (semgrep.sarif, race tests)\n" >> docs/PROOFS_INDEX.md
	@printf -- "- Fortress Suite → docs/proofs/suite/\n" >> docs/PROOFS_INDEX.md

clean:
	docker compose down -v || true
	rm -rf docs/proofs/anchoring docs/proofs/custody docs/proofs/suite

# ---------- CI canonical artifacts ----------
# (CI workflows emit artifacts. Local `make` is not a source of truth.)

# ---- SnapSec DB + tests + server ----
snapsec-db-init:
	psql "postgresql://root@localhost:26257?sslmode=disable" \
	 -c "CREATE DATABASE IF NOT EXISTS snapsec;"
	psql "postgresql://root@localhost:26257/snapsec?sslmode=disable" \
	 -f services/snapsec/schema.sql

snapsec-race:
	go test ./services/snapsec/tests -race -count=1

snapsec-server:
	go run ./services/snapsec/cmd/server