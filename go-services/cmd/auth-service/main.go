package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"webapp-go-services/internal/common/app"
	commonauth "webapp-go-services/internal/common/auth"
	mongostore "webapp-go-services/internal/common/mongo"
)

type credentials struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type changePasswordRequest struct {
	CurrentPassword string `json:"current_password"`
	NewPassword     string `json:"new_password"`
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()

	store, err := mongostore.Connect(ctx)
	if err != nil {
		panic(err)
	}
	ensureAdmin(ctx, store)

	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", app.HealthHandler("auth-go"))
	mux.HandleFunc("POST /api/register", registerHandler(store))
	mux.HandleFunc("POST /api/login", loginHandler(store))
	mux.Handle("GET /api/me", commonauth.RequireUser(store, meHandler))
	mux.Handle("POST /api/change-password", commonauth.RequireUser(store, changePasswordHandler(store)))
	mux.HandleFunc("GET /api/weather", weatherHandler)

	app.ListenAndServe("auth-go", mux)
}

func registerHandler(store *mongostore.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var input credentials
		if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный JSON")
			return
		}
		input.Username = strings.TrimSpace(input.Username)
		if len(input.Username) < 3 || len(input.Username) > 30 {
			app.Error(w, http.StatusBadRequest, "Имя пользователя должно содержать от 3 до 30 символов")
			return
		}
		if len(input.Password) < 6 {
			app.Error(w, http.StatusBadRequest, "Пароль должен содержать минимум 6 символов")
			return
		}

		existing := store.Users.FindOne(r.Context(), bson.M{"username": input.Username})
		if existing.Err() == nil {
			app.Error(w, http.StatusBadRequest, "Пользователь с таким именем уже существует")
			return
		}
		if existing.Err() != mongo.ErrNoDocuments {
			app.Error(w, http.StatusInternalServerError, "Ошибка базы данных")
			return
		}

		hash, err := commonauth.HashPassword(input.Password)
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Не удалось создать пароль")
			return
		}
		_, err = store.Users.InsertOne(r.Context(), bson.M{
			"username":        input.Username,
			"email":           nil,
			"hashed_password": hash,
			"is_admin":        false,
			"created_at":      time.Now().UTC(),
		})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка сохранения пользователя")
			return
		}

		token, err := commonauth.CreateToken(input.Username, false, 7*24*time.Hour)
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка токена")
			return
		}

		app.JSON(w, http.StatusOK, map[string]any{
			"access_token": token,
			"token_type":   "bearer",
			"username":     input.Username,
			"is_admin":     false,
		})
	}
}

func loginHandler(store *mongostore.Store) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var input credentials
		if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный JSON")
			return
		}
		input.Username = strings.TrimSpace(input.Username)

		var user commonauth.User
		if err := store.Users.FindOne(r.Context(), bson.M{"username": input.Username}).Decode(&user); err != nil {
			app.Error(w, http.StatusUnauthorized, "Неверное имя пользователя или пароль")
			return
		}
		if !commonauth.VerifyPassword(input.Password, user.HashedPassword) {
			app.Error(w, http.StatusUnauthorized, "Неверное имя пользователя или пароль")
			return
		}

		ttl := 7 * 24 * time.Hour
		if user.IsAdmin {
			ttl = 30 * time.Minute
		}
		token, err := commonauth.CreateToken(user.Username, user.IsAdmin, ttl)
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка токена")
			return
		}

		app.JSON(w, http.StatusOK, map[string]any{
			"access_token": token,
			"token_type":   "bearer",
			"username":     user.Username,
			"is_admin":     user.IsAdmin,
		})
	}
}

func meHandler(w http.ResponseWriter, r *http.Request, user commonauth.User) {
	app.JSON(w, http.StatusOK, map[string]any{
		"username": user.Username,
		"email":    user.Email,
		"is_admin": user.IsAdmin,
	})
}

func changePasswordHandler(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, user commonauth.User) {
		var input changePasswordRequest
		if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный JSON")
			return
		}
		if !commonauth.VerifyPassword(input.CurrentPassword, user.HashedPassword) {
			app.Error(w, http.StatusBadRequest, "Неверный текущий пароль")
			return
		}
		if len(input.NewPassword) < 6 {
			app.Error(w, http.StatusBadRequest, "Новый пароль должен содержать минимум 6 символов")
			return
		}
		if input.CurrentPassword == input.NewPassword {
			app.Error(w, http.StatusBadRequest, "Новый пароль должен отличаться от текущего")
			return
		}
		hash, err := commonauth.HashPassword(input.NewPassword)
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Не удалось обновить пароль")
			return
		}
		_, err = store.Users.UpdateByID(r.Context(), user.ID, bson.M{"$set": bson.M{"hashed_password": hash}})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка обновления пароля")
			return
		}
		app.JSON(w, http.StatusOK, map[string]any{"success": true, "message": "Пароль успешно изменён"})
	}
}

func weatherHandler(w http.ResponseWriter, r *http.Request) {
	city := strings.TrimSpace(r.URL.Query().Get("city"))
	if city == "" {
		city = envDefault("WEATHER_CITY", "Moscow")
	}
	apiKey := os.Getenv("OPENWEATHER_API_KEY")
	if apiKey == "" {
		app.JSON(w, http.StatusOK, map[string]any{"city": city, "temp_c": nil, "description": "NO OPENWEATHER_API_KEY in .env", "icon_url": nil})
		return
	}

	endpoint := fmt.Sprintf("https://api.openweathermap.org/data/2.5/weather?q=%s&appid=%s&units=metric&lang=ru", url.QueryEscape(city), url.QueryEscape(apiKey))
	req, _ := http.NewRequestWithContext(r.Context(), http.MethodGet, endpoint, nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		app.JSON(w, http.StatusOK, map[string]any{"city": city, "temp_c": nil, "description": "Error: " + err.Error(), "icon_url": nil})
		return
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)

	var payload struct {
		Main struct {
			Temp float64 `json:"temp"`
		} `json:"main"`
		Weather []struct {
			Description string `json:"description"`
			Icon        string `json:"icon"`
		} `json:"weather"`
	}
	if err := json.Unmarshal(body, &payload); err != nil {
		app.JSON(w, http.StatusOK, map[string]any{"city": city, "temp_c": nil, "description": "Error: " + err.Error(), "icon_url": nil})
		return
	}
	iconURL := any(nil)
	description := any(nil)
	if len(payload.Weather) > 0 {
		description = payload.Weather[0].Description
		if payload.Weather[0].Icon != "" {
			iconURL = "https://openweathermap.org/img/wn/" + payload.Weather[0].Icon + "@2x.png"
		}
	}
	app.JSON(w, http.StatusOK, map[string]any{"city": city, "temp_c": payload.Main.Temp, "description": description, "icon_url": iconURL})
}

func ensureAdmin(ctx context.Context, store *mongostore.Store) {
	username := envDefault("DEFAULT_ADMIN_USERNAME", "admin")
	password := envDefault("DEFAULT_ADMIN_PASSWORD", "admin123")

	var user commonauth.User
	err := store.Users.FindOne(ctx, bson.M{"username": username}).Decode(&user)
	if err == nil {
		if !user.IsAdmin {
			_, _ = store.Users.UpdateByID(ctx, user.ID, bson.M{"$set": bson.M{"is_admin": true}})
		}
		return
	}
	hash, err := commonauth.HashPassword(password)
	if err != nil {
		return
	}
	_, _ = store.Users.InsertOne(ctx, bson.M{
		"username":        username,
		"email":           nil,
		"hashed_password": hash,
		"is_admin":        true,
		"created_at":      time.Now().UTC(),
	})
}

func envDefault(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
