package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	commonauth "webapp-go-services/internal/common/auth"
)

func TestWeatherHandlerWithoutAPIKeyReturnsStub(t *testing.T) {
	t.Setenv("OPENWEATHER_API_KEY", "")
	t.Setenv("WEATHER_CITY", "Moscow")

	req := httptest.NewRequest(http.MethodGet, "/api/weather", nil)
	rec := httptest.NewRecorder()

	weatherHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}

	var payload map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &payload); err != nil {
		t.Fatalf("unmarshal response: %v", err)
	}
	if payload["city"] != "Moscow" {
		t.Fatalf("expected city Moscow, got %#v", payload["city"])
	}
	if payload["temp_c"] != nil {
		t.Fatalf("expected nil temp_c, got %#v", payload["temp_c"])
	}
}

func TestMeHandlerReturnsCurrentUser(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/api/me", nil)
	rec := httptest.NewRecorder()
	user := commonauth.User{Username: "alice", IsAdmin: true}

	meHandler(rec, req, user)

	if rec.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rec.Code)
	}

	var payload map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &payload); err != nil {
		t.Fatalf("unmarshal response: %v", err)
	}
	if payload["username"] != "alice" {
		t.Fatalf("expected username alice, got %#v", payload["username"])
	}
	if payload["is_admin"] != true {
		t.Fatalf("expected is_admin true, got %#v", payload["is_admin"])
	}
}
