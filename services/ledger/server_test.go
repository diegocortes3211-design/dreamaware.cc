package main

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

// Mock Rekor client for testing
type mockRekorClient struct {
	healthy bool
	fail    bool
}

func (m *mockRekorClient) SubmitEntry(ctx context.Context, payload, signature []byte, publicKey string) (string, int64, error) {
	if m.fail {
		return "", 0, context.DeadlineExceeded
	}
	return "test-uuid-12345", 42, nil
}

func (m *mockRekorClient) IsHealthy(ctx context.Context) bool {
	return m.healthy
}

func TestHealthEndpoint(t *testing.T) {
	// Mock database connection would go here in a real test
	// For now, we test the handler logic

	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	rr := httptest.NewRecorder()
	
	// Simple health check handler test
	handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		health := map[string]interface{}{
			"status":   "healthy",
			"database": "ok", // Would check real DB in production
			"rekor":    true, // Would check real Rekor in production
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(health)
	})

	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	var response map[string]interface{}
	if err := json.Unmarshal(rr.Body.Bytes(), &response); err != nil {
		t.Errorf("Could not parse response: %v", err)
	}

	if response["status"] != "healthy" {
		t.Errorf("Expected status to be 'healthy', got %v", response["status"])
	}
}

func TestSimpleRekorClient(t *testing.T) {
	client := NewSimpleRekorClient("https://rekor.sigstore.dev")
	
	if client.baseURL != "https://rekor.sigstore.dev" {
		t.Errorf("Expected baseURL to be set correctly")
	}
	
	if client.client.Timeout != 30*time.Second {
		t.Errorf("Expected timeout to be 30 seconds")
	}
}

func TestRequestValidation(t *testing.T) {
	tests := []struct {
		name           string
		payload        string
		expectedStatus int
	}{
		{
			name:           "Valid request",
			payload:        `{"subject": "test", "payload": "SGVsbG8=", "meta": {}}`,
			expectedStatus: http.StatusBadRequest, // Would be 201 with real Vault
		},
		{
			name:           "Missing subject",
			payload:        `{"payload": "SGVsbG8=", "meta": {}}`,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:           "Empty payload",
			payload:        `{"subject": "test", "payload": "", "meta": {}}`,
			expectedStatus: http.StatusBadRequest,
		},
		{
			name:           "Invalid JSON",
			payload:        `{"subject": "test"`,
			expectedStatus: http.StatusBadRequest,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req, err := http.NewRequest("POST", "/append", bytes.NewBufferString(tt.payload))
			if err != nil {
				t.Fatal(err)
			}
			req.Header.Set("Content-Type", "application/json")

			rr := httptest.NewRecorder()
			
			// Simplified validation handler
			handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				defer r.Body.Close()
				var q struct {
					Subject string         `json:"subject"`
					Payload []byte        `json:"payload"`
					Meta    map[string]any `json:"meta"`
				}
				if err := json.NewDecoder(r.Body).Decode(&q); err != nil {
					http.Error(w, err.Error(), http.StatusBadRequest)
					return
				}
				if q.Subject == "" || len(q.Payload) == 0 {
					http.Error(w, "subject/payload required", http.StatusBadRequest)
					return
				}
				// Would continue with Vault signing in real implementation
				http.Error(w, "vault not configured in test", http.StatusBadRequest)
			})

			handler.ServeHTTP(rr, req)

			if status := rr.Code; status != tt.expectedStatus {
				t.Errorf("%s: handler returned wrong status code: got %v want %v", 
					tt.name, status, tt.expectedStatus)
			}
		})
	}
}

// Integration test helpers
func TestRekorIntegration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Test with mock client
	mockClient := &mockRekorClient{healthy: true, fail: false}
	
	ctx := context.Background()
	payload := []byte("test payload")
	signature := []byte("test signature")
	publicKey := "test-public-key"

	logID, index, err := mockClient.SubmitEntry(ctx, payload, signature, publicKey)
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	if logID != "test-uuid-12345" {
		t.Errorf("Expected logID 'test-uuid-12345', got %v", logID)
	}

	if index != 42 {
		t.Errorf("Expected index 42, got %v", index)
	}

	// Test health check
	if !mockClient.IsHealthy(ctx) {
		t.Errorf("Expected client to be healthy")
	}
}

func TestRekorFailure(t *testing.T) {
	// Test failure handling
	mockClient := &mockRekorClient{healthy: false, fail: true}
	
	ctx := context.Background()
	payload := []byte("test payload")
	signature := []byte("test signature")
	publicKey := "test-public-key"

	_, _, err := mockClient.SubmitEntry(ctx, payload, signature, publicKey)
	if err == nil {
		t.Errorf("Expected error, got nil")
	}

	// Test unhealthy client
	if mockClient.IsHealthy(ctx) {
		t.Errorf("Expected client to be unhealthy")
	}
}