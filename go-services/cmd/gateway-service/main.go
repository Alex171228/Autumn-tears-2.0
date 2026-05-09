package main

import (
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"

	"webapp-go-services/internal/common/app"
)

type targetRoute struct {
	Prefix string
	URL    string
}

func main() {
	routes := []targetRoute{
		{Prefix: "/api/register", URL: envDefault("AUTH_SERVICE_URL", "http://auth-service-go:8000")},
		{Prefix: "/api/login", URL: envDefault("AUTH_SERVICE_URL", "http://auth-service-go:8000")},
		{Prefix: "/api/me", URL: envDefault("AUTH_SERVICE_URL", "http://auth-service-go:8000")},
		{Prefix: "/api/change-password", URL: envDefault("AUTH_SERVICE_URL", "http://auth-service-go:8000")},
		{Prefix: "/api/weather", URL: envDefault("AUTH_SERVICE_URL", "http://auth-service-go:8000")},
		{Prefix: "/api/robot/", URL: envDefault("SIMULATION_SERVICE_URL", "http://simulation-engine:8000")},
		{Prefix: "/api/configs", URL: envDefault("CONFIG_SERVICE_URL", "http://config-service-go:8000")},
		{Prefix: "/api/data/", URL: envDefault("CONFIG_SERVICE_URL", "http://config-service-go:8000")},
		{Prefix: "/api/admin/", URL: envDefault("ADMIN_SERVICE_URL", "http://admin-service-go:8000")},
	}
	frontendURL := envDefault("FRONTEND_URL", "http://frontend:80")

	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", app.HealthHandler("gateway-go"))
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		target := resolveTarget(routes, r.URL.Path, frontendURL)
		reverseProxy(target).ServeHTTP(w, r)
	})
	app.ListenAndServe("gateway-go", mux)
}

func resolveTarget(routes []targetRoute, path, frontendURL string) string {
	for _, route := range routes {
		if path == route.Prefix || strings.HasPrefix(path, route.Prefix) {
			return route.URL
		}
	}
	return frontendURL
}

func reverseProxy(rawURL string) *httputil.ReverseProxy {
	target, err := url.Parse(rawURL)
	if err != nil {
		panic(err)
	}
	proxy := httputil.NewSingleHostReverseProxy(target)
	originalDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		originalDirector(req)
		req.Header.Set("X-Forwarded-Proto", "http")
		if req.Host != "" {
			req.Header.Set("X-Forwarded-Host", req.Host)
		}
	}
	return proxy
}

func envDefault(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
