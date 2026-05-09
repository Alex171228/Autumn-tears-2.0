package auth

import (
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestHashAndVerifyPassword(t *testing.T) {
	hash, err := HashPassword("secret123")
	if err != nil {
		t.Fatalf("hash password: %v", err)
	}
	if !VerifyPassword("secret123", hash) {
		t.Fatal("expected password verification to succeed")
	}
	if VerifyPassword("wrong", hash) {
		t.Fatal("expected wrong password verification to fail")
	}
}

func TestCreateAndParseToken(t *testing.T) {
	t.Setenv("SECRET_KEY", "test-secret")

	token, err := CreateToken("alice", true, time.Hour)
	if err != nil {
		t.Fatalf("create token: %v", err)
	}
	claims, err := ParseToken(token)
	if err != nil {
		t.Fatalf("parse token: %v", err)
	}
	if claims.Subject != "alice" {
		t.Fatalf("expected subject alice, got %q", claims.Subject)
	}
	if !claims.IsAdmin {
		t.Fatal("expected admin claim to be true")
	}
}

func TestBearerToken(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	req.Header.Set("Authorization", "Bearer abc123")

	token, err := BearerToken(req)
	if err != nil {
		t.Fatalf("bearer token: %v", err)
	}
	if token != "abc123" {
		t.Fatalf("expected token abc123, got %q", token)
	}
}

func TestBearerTokenRequiresHeader(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/", nil)
	if _, err := BearerToken(req); err == nil {
		t.Fatal("expected missing header error")
	}
}
