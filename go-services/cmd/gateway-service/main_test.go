package main

import "testing"

func TestResolveTargetMatchesKnownPrefixes(t *testing.T) {
	routes := []targetRoute{
		{Prefix: "/api/login", URL: "http://auth"},
		{Prefix: "/api/robot/", URL: "http://simulation"},
		{Prefix: "/api/admin/", URL: "http://admin"},
	}

	if got := resolveTarget(routes, "/api/login", "http://frontend"); got != "http://auth" {
		t.Fatalf("expected auth target, got %q", got)
	}
	if got := resolveTarget(routes, "/api/robot/state", "http://frontend"); got != "http://simulation" {
		t.Fatalf("expected simulation target, got %q", got)
	}
	if got := resolveTarget(routes, "/api/admin/users", "http://frontend"); got != "http://admin" {
		t.Fatalf("expected admin target, got %q", got)
	}
}

func TestResolveTargetFallsBackToFrontend(t *testing.T) {
	routes := []targetRoute{
		{Prefix: "/api/login", URL: "http://auth"},
	}

	if got := resolveTarget(routes, "/", "http://frontend"); got != "http://frontend" {
		t.Fatalf("expected frontend target, got %q", got)
	}
	if got := resolveTarget(routes, "/assets/main.js", "http://frontend"); got != "http://frontend" {
		t.Fatalf("expected frontend target, got %q", got)
	}
}
