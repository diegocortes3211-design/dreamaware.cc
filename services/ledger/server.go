package main

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"errors"
	"log"
	"net/http"
	"os"
	"strings"
	"time"
	_ "github.com/jackc/pgx/v5/stdlib"
)

type req struct {
	Subject string         `json:"subject"`
	Payload []byte        `json:"payload"` // base64-encoded in JSON
	Meta    map[string]any `json:"meta"`
}

type vaultSignResp struct {
	Data struct {
		Signature string `json:"signature"` // vault:v1:<base64 sig>
		PublicKey string `json:"public_key"` // base64
	} `json:"data"`
}

func main() {
	dsn := getenv("CRDB_DSN", "postgresql://root@localhost:26257/ledger?sslmode=disable")
	db, err := sql.Open("pgx", dsn)
	must(err)
	must(db.Ping())

	http.HandleFunc("/append", func(w http.ResponseWriter, r *http.Request) {
		defer r.Body.Close()
		var q req
		if err := json.NewDecoder(r.Body).Decode(&q); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}
		if q.Subject == "" || len(q.Payload) == 0 {
			http.Error(w, "subject/payload required", http.StatusBadRequest)
			return
		}

		// Vault Transit Ed25519 sign
		sig, pub, err := vaultSign(q.Payload)
		if err != nil {
			http.Error(w, "vault sign: "+err.Error(), http.StatusInternalServerError)
			return
		}

		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		tx, err := db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelSerializable})
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		defer func() { _ = tx.Rollback() }()

		_, err = tx.ExecContext(ctx, `
			INSERT INTO ledger.entries (subject,payload,sig,pubkey,meta)
			VALUES ($1,$2,$3,$4,$5)
		`, q.Subject, q.Payload, sig, pub, toJSON(q.Meta))
		if err != nil {
			http.Error(w, err.Error(), 500)
			return
		}
		must(tx.Commit())
		w.WriteHeader(http.StatusCreated)
	})

	log.Println("ledger listening :8088")
	log.Fatal(http.ListenAndServe(":8088", nil))
}

func vaultSign(payload []byte) ([]byte, string, error) {
	url := os.Getenv("VAULT_ADDR")
	token := os.Getenv("VAULT_TOKEN")
	key := os.Getenv("VAULT_TRANSIT_KEY") // e.g., ledger-ed25519
	if url == "" || token == "" || key == "" {
		return nil, "", errors.New("VAULT_* env not set")
	}

	reqBody := map[string]any{
		"input": base64.StdEncoding.EncodeToString(payload),
		"prehashed": false,
		"signature_algorithm": "ed25519",
	}
	rb, _ := json.Marshal(reqBody)
	httpReq, _ := http.NewRequest("POST", strings.TrimRight(url, "/")+"/v1/transit/sign/"+key, bytes.NewReader(rb))
	httpReq.Header.Set("X-Vault-Token", token)
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := http.DefaultClient.Do(httpReq)
	if err != nil {
		return nil, "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode/100 != 2 {
		return nil, "", errors.New("vault transit non-2xx")
	}

	var vr vaultSignResp
	if err := json.NewDecoder(resp.Body).Decode(&vr); err != nil {
		return nil, "", err
	}

	parts := strings.Split(vr.Data.Signature, ":")
	if len(parts) != 3 {
		return nil, "", errors.New("bad vault signature")
	}
	sigBytes, err := base64.StdEncoding.DecodeString(parts[2])
	if err != nil {
		return nil, "", err
	}

	pkBytes, err := base64.StdEncoding.DecodeString(vr.Data.PublicKey)
	if err != nil {
		return nil, "", err
	}

	if len(pkBytes) == ed25519.PublicKeySize && !ed25519.Verify(ed25519.PublicKey(pkBytes), payload, sigBytes) {
		return nil, "", errors.New("local ed25519 verify failed")
	}

	return sigBytes, vr.Data.PublicKey, nil
}

func toJSON(m map[string]any) []byte { b, _ := json.Marshal(m); return b }

func must(err error) { if err != nil { log.Fatal(err) } }

func getenv(k, d string) string { if v := os.Getenv(k); v != ""; return v }; return d }