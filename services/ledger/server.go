package main

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/sha256"
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	_ "github.com/jackc/pgx/v5/stdlib"
)

type RekorClient interface {
	SubmitEntry(ctx context.Context, payload, signature []byte, publicKey string) (logID string, index int64, err error)
	IsHealthy(ctx context.Context) bool
}

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

type ledgerEntry struct {
	ID           int64     `json:"id"`
	Subject      string    `json:"subject"`
	PayloadHash  string    `json:"payload_hash"`
	Signature    string    `json:"signature"`
	PublicKey    string    `json:"public_key"`
	RekorLogID   string    `json:"rekor_log_id,omitempty"`
	RekorIndex   int64     `json:"rekor_index,omitempty"`
	CreatedAt    time.Time `json:"created_at"`
	AnchoredAt   *time.Time `json:"anchored_at,omitempty"`
}

func main() {
	dsn := getenv("CRDB_DSN", "postgresql://root@localhost:26257/ledger?sslmode=disable")
	db, err := sql.Open("pgx", dsn)
	must(err)
	must(db.Ping())

	// Initialize database schema
	must(initSchema(db))

	// Initialize Rekor client (simplified for now)
	var rekorClient RekorClient
	rekorURL := getenv("REKOR_SERVER_URL", "https://rekor.sigstore.dev")
	if rekorURL != "" {
		rekorClient = NewSimpleRekorClient(rekorURL)
		log.Printf("Rekor client initialized for %s", rekorURL)
	} else {
		log.Println("Warning: Rekor client not initialized (REKOR_SERVER_URL not set)")
	}

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

		// Hash the payload for storage (don't store sensitive data)
		payloadHash := sha256.Sum256(q.Payload)
		payloadHashHex := hex.EncodeToString(payloadHash[:])

		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second) // Increased timeout for Rekor
		defer cancel()

		tx, err := db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelSerializable})
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		defer func() { _ = tx.Rollback() }()

		var entryID int64
		err = tx.QueryRowContext(ctx, `
			INSERT INTO ledger.entries (subject, payload_hash, sig, pubkey, meta)
			VALUES ($1, $2, $3, $4, $5)
			RETURNING id
		`, q.Subject, payloadHashHex, base64.StdEncoding.EncodeToString(sig), pub, toJSON(q.Meta)).Scan(&entryID)
		if err != nil {
			http.Error(w, "database error: "+err.Error(), http.StatusInternalServerError)
			return
		}

		// Commit transaction first to ensure data persistence
		if err := tx.Commit(); err != nil {
			http.Error(w, "commit error: "+err.Error(), http.StatusInternalServerError)
			return
		}

		// Async Rekor anchoring (don't block the response)
		if rekorClient != nil {
			go func() {
				if err := anchorToRekor(db, rekorClient, entryID, q.Payload, sig, pub); err != nil {
					log.Printf("Rekor anchoring failed for entry %d: %v", entryID, err)
				}
			}()
		}

		entry := ledgerEntry{
			ID:          entryID,
			Subject:     q.Subject,
			PayloadHash: payloadHashHex,
			Signature:   base64.StdEncoding.EncodeToString(sig),
			PublicKey:   pub,
			CreatedAt:   time.Now(),
		}

		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusCreated)
		json.NewEncoder(w).Encode(entry)
	})

	http.HandleFunc("/entries", func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		rows, err := db.QueryContext(ctx, `
			SELECT id, subject, payload_hash, sig, pubkey, 
			       COALESCE(rekor_log_id, ''), COALESCE(rekor_index, 0),
			       created_at, anchored_at
			FROM ledger.entries 
			ORDER BY id DESC LIMIT 100
		`)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		defer rows.Close()

		var entries []ledgerEntry
		for rows.Next() {
			var entry ledgerEntry
			var anchoredAt sql.NullTime
			err := rows.Scan(&entry.ID, &entry.Subject, &entry.PayloadHash, 
				&entry.Signature, &entry.PublicKey, &entry.RekorLogID, 
				&entry.RekorIndex, &entry.CreatedAt, &anchoredAt)
			if err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			if anchoredAt.Valid {
				entry.AnchoredAt = &anchoredAt.Time
			}
			entries = append(entries, entry)
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(entries)
	})

	http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()

		// Check database
		if err := db.PingContext(ctx); err != nil {
			http.Error(w, "database unhealthy: "+err.Error(), http.StatusServiceUnavailable)
			return
		}

		// Check Rekor connectivity
		rekorHealthy := false
		if rekorClient != nil {
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			rekorHealthy = rekorClient.IsHealthy(ctx)
		}

		health := map[string]interface{}{
			"status":   "healthy",
			"database": "ok",
			"rekor":    rekorHealthy,
		}

		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(health)
	})

	log.Println("ledger listening :8088")
	log.Fatal(http.ListenAndServe(":8088", nil))
}

func initSchema(db *sql.DB) error {
	schema := `
		CREATE SCHEMA IF NOT EXISTS ledger;
		CREATE TABLE IF NOT EXISTS ledger.entries (
			id SERIAL PRIMARY KEY,
			subject TEXT NOT NULL,
			payload_hash TEXT NOT NULL,
			sig TEXT NOT NULL,
			pubkey TEXT NOT NULL,
			meta JSONB DEFAULT '{}',
			rekor_log_id TEXT DEFAULT '',
			rekor_index BIGINT DEFAULT 0,
			created_at TIMESTAMP DEFAULT NOW(),
			anchored_at TIMESTAMP NULL
		);
		CREATE INDEX IF NOT EXISTS idx_entries_subject ON ledger.entries(subject);
		CREATE INDEX IF NOT EXISTS idx_entries_created ON ledger.entries(created_at);
		CREATE INDEX IF NOT EXISTS idx_entries_rekor ON ledger.entries(rekor_log_id) WHERE rekor_log_id != '';
	`
	_, err := db.Exec(schema)
	return err
}

func anchorToRekor(db *sql.DB, rekorClient RekorClient, entryID int64, payload, signature []byte, publicKey string) error {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// Submit to Rekor
	rekorLogID, rekorIndex, err := rekorClient.SubmitEntry(ctx, payload, signature, publicKey)
	if err != nil {
		return fmt.Errorf("submit to rekor: %w", err)
	}

	// Update database with Rekor information
	_, err = db.ExecContext(ctx, `
		UPDATE ledger.entries 
		SET rekor_log_id = $1, rekor_index = $2, anchored_at = NOW()
		WHERE id = $3
	`, rekorLogID, rekorIndex, entryID)
	
	if err != nil {
		return fmt.Errorf("update database with rekor info: %w", err)
	}

	log.Printf("Entry %d anchored to Rekor: logID=%s, index=%d", entryID, rekorLogID, rekorIndex)
	return nil
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
	
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	
	httpReq, err := http.NewRequestWithContext(ctx, "POST", strings.TrimRight(url, "/")+"/v1/transit/sign/"+key, bytes.NewReader(rb))
	if err != nil {
		return nil, "", err
	}
	
	httpReq.Header.Set("X-Vault-Token", token)
	httpReq.Header.Set("Content-Type", "application/json")

	client := &http.Client{
		Timeout: 10 * time.Second,
	}
	
	resp, err := client.Do(httpReq)
	if err != nil {
		return nil, "", err
	}
	defer resp.Body.Close()
	
	if resp.StatusCode/100 != 2 {
		return nil, "", fmt.Errorf("vault transit non-2xx: %d", resp.StatusCode)
	}

	var vr vaultSignResp
	if err := json.NewDecoder(resp.Body).Decode(&vr); err != nil {
		return nil, "", err
	}

	parts := strings.Split(vr.Data.Signature, ":")
	if len(parts) != 3 {
		return nil, "", errors.New("bad vault signature format")
	}
	
	sigBytes, err := base64.StdEncoding.DecodeString(parts[2])
	if err != nil {
		return nil, "", fmt.Errorf("decode signature: %w", err)
	}

	pkBytes, err := base64.StdEncoding.DecodeString(vr.Data.PublicKey)
	if err != nil {
		return nil, "", fmt.Errorf("decode public key: %w", err)
	}

	// Verify signature locally before proceeding
	if len(pkBytes) == ed25519.PublicKeySize && !ed25519.Verify(ed25519.PublicKey(pkBytes), payload, sigBytes) {
		return nil, "", errors.New("local ed25519 verify failed")
	}

	return sigBytes, vr.Data.PublicKey, nil
}

func toJSON(m map[string]any) []byte { 
	b, _ := json.Marshal(m) 
	return b 
}

func must(err error) { 
	if err != nil { 
		log.Fatal(err) 
	} 
}

func getenv(k, d string) string { 
	if v := os.Getenv(k); v != "" { 
		return v 
	}
	return d 
}

// SimpleRekorClient implements basic Rekor functionality via HTTP API
type SimpleRekorClient struct {
	baseURL string
	client  *http.Client
}

func NewSimpleRekorClient(baseURL string) *SimpleRekorClient {
	return &SimpleRekorClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (r *SimpleRekorClient) SubmitEntry(ctx context.Context, payload, signature []byte, publicKey string) (string, int64, error) {
	// Hash the payload
	payloadHash := sha256.Sum256(payload)
	
	// Create hashedrekord entry
	entry := map[string]interface{}{
		"apiVersion": "0.0.1",
		"kind":       "hashedrekord",
		"spec": map[string]interface{}{
			"data": map[string]interface{}{
				"hash": map[string]interface{}{
					"algorithm": "sha256",
					"value":     hex.EncodeToString(payloadHash[:]),
				},
			},
			"signature": map[string]interface{}{
				"content": base64.StdEncoding.EncodeToString(signature),
				"publicKey": map[string]interface{}{
					"content": publicKey,
				},
			},
		},
	}

	entryBytes, err := json.Marshal(entry)
	if err != nil {
		return "", 0, fmt.Errorf("marshal entry: %w", err)
	}

	// Submit to Rekor
	req, err := http.NewRequestWithContext(ctx, "POST", r.baseURL+"/api/v1/log/entries", bytes.NewReader(entryBytes))
	if err != nil {
		return "", 0, fmt.Errorf("create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Accept", "application/json")

	resp, err := r.client.Do(req)
	if err != nil {
		return "", 0, fmt.Errorf("http request: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusCreated {
		return "", 0, fmt.Errorf("rekor returned status %d", resp.StatusCode)
	}

	// Parse response
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", 0, fmt.Errorf("decode response: %w", err)
	}

	// Extract log ID and index (simplified)
	var logID string
	var logIndex int64
	
	// The response structure varies, but typically contains the entry UUID and log index
	for k, v := range result {
		logID = k // Use the first key as log ID
		if entry, ok := v.(map[string]interface{}); ok {
			if idx, ok := entry["logIndex"].(float64); ok {
				logIndex = int64(idx)
			}
		}
		break
	}

	return logID, logIndex, nil
}

func (r *SimpleRekorClient) IsHealthy(ctx context.Context) bool {
	req, err := http.NewRequestWithContext(ctx, "GET", r.baseURL+"/api/v1/log", nil)
	if err != nil {
		return false
	}

	resp, err := r.client.Do(req)
	if err != nil {
		return false
	}
	defer resp.Body.Close()

	return resp.StatusCode == http.StatusOK
}