package app

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"
)

type jsonError struct {
	Detail string `json:"detail"`
}

func WithCommonMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS, HEAD")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}

		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %s", r.Method, r.URL.Path, time.Since(start))
	})
}

func JSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	if payload == nil {
		return
	}
	_ = json.NewEncoder(w).Encode(payload)
}

func Error(w http.ResponseWriter, status int, detail string) {
	JSON(w, status, jsonError{Detail: detail})
}

func HealthHandler(service string) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		JSON(w, http.StatusOK, map[string]any{
			"ok":      true,
			"service": service,
			"time":    time.Now().UTC().Format(time.RFC3339),
		})
	}
}

func ListenAndServe(service string, handler http.Handler) {
	addr := ":" + envDefault("PORT", "8000")
	log.Printf("%s listening on %s", service, addr)
	log.Fatal(http.ListenAndServe(addr, WithCommonMiddleware(handler)))
}

func envDefault(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
