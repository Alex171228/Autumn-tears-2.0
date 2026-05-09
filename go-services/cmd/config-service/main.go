package main

import (
	"context"
	"encoding/json"
	"io"
	"mime/multipart"
	"net/http"
	"strings"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"webapp-go-services/internal/common/app"
	commonauth "webapp-go-services/internal/common/auth"
	"webapp-go-services/internal/common/configfiles"
	mongostore "webapp-go-services/internal/common/mongo"
)

type configPayload struct {
	Name       string         `bson:"name" json:"name"`
	ConfigData map[string]any `bson:"config_data" json:"config_data"`
}

type savedConfig struct {
	ID         primitive.ObjectID `bson:"_id,omitempty"`
	UserID     string             `bson:"user_id"`
	Name       string             `bson:"name"`
	ConfigData map[string]any     `bson:"config_data"`
	CreatedAt  time.Time          `bson:"created_at"`
	UpdatedAt  time.Time          `bson:"updated_at"`
}

func main() {
	store, err := mongostore.Connect(context.Background())
	if err != nil {
		panic(err)
	}

	mux := http.NewServeMux()
	mux.HandleFunc("GET /healthz", app.HealthHandler("config-go"))
	mux.HandleFunc("POST /api/data/upload", uploadConfigFile)
	mux.HandleFunc("POST /api/data/download", downloadConfigFile)
	mux.Handle("GET /api/configs", commonauth.RequireUser(store, listConfigs(store)))
	mux.Handle("GET /api/configs/{configID}", commonauth.RequireUser(store, getConfig(store)))
	mux.Handle("POST /api/configs", commonauth.RequireUser(store, saveConfig(store)))
	mux.Handle("PUT /api/configs/{configID}", commonauth.RequireUser(store, updateConfig(store)))
	mux.Handle("DELETE /api/configs/{configID}", commonauth.RequireUser(store, deleteConfig(store)))

	app.ListenAndServe("config-go", mux)
}

func uploadConfigFile(w http.ResponseWriter, r *http.Request) {
	file, _, err := r.FormFile("file")
	if err != nil {
		app.Error(w, http.StatusBadRequest, "Файл не загружен")
		return
	}
	defer file.Close()

	content, err := readAll(file)
	if err != nil {
		app.Error(w, http.StatusBadRequest, "Не удалось прочитать файл")
		return
	}
	text, err := configfiles.DecodeFile(content)
	if err != nil {
		app.Error(w, http.StatusBadRequest, err.Error())
		return
	}
	config := configfiles.Parse(text)
	app.JSON(w, http.StatusOK, map[string]any{
		"success":  true,
		"message":  "Файл успешно загружен",
		"filename": "robot_config.txt",
		"state":    configfiles.ToFrontendState(config),
	})
}

func downloadConfigFile(w http.ResponseWriter, r *http.Request) {
	var state map[string]any
	if err := json.NewDecoder(r.Body).Decode(&state); err != nil {
		app.Error(w, http.StatusBadRequest, "Некорректный JSON")
		return
	}
	content, err := configfiles.EncodeWindows1251(configfiles.Generate(state))
	if err != nil {
		app.Error(w, http.StatusInternalServerError, "Ошибка генерации файла")
		return
	}
	w.Header().Set("Content-Type", "text/plain; charset=windows-1251")
	w.Header().Set("Content-Disposition", "attachment; filename=robot_config.txt")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(content)
}

func listConfigs(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, user commonauth.User) {
		cursor, err := store.SavedConfigs.Find(r.Context(), bson.M{"user_id": user.ID.Hex()})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка чтения конфигураций")
			return
		}
		defer cursor.Close(r.Context())
		var configs []savedConfig
		if err := cursor.All(r.Context(), &configs); err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка чтения конфигураций")
			return
		}
		result := make([]map[string]any, 0, len(configs))
		for _, cfg := range configs {
			result = append(result, map[string]any{
				"id":         cfg.ID.Hex(),
				"name":       cfg.Name,
				"created_at": cfg.CreatedAt.Format(time.RFC3339),
				"updated_at": cfg.UpdatedAt.Format(time.RFC3339),
			})
		}
		app.JSON(w, http.StatusOK, result)
	}
}

func getConfig(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, user commonauth.User) {
		id, err := primitive.ObjectIDFromHex(r.PathValue("configID"))
		if err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный ID конфигурации")
			return
		}
		var cfg savedConfig
		err = store.SavedConfigs.FindOne(r.Context(), bson.M{"_id": id, "user_id": user.ID.Hex()}).Decode(&cfg)
		if err != nil {
			app.Error(w, http.StatusNotFound, "Конфигурация не найдена")
			return
		}
		app.JSON(w, http.StatusOK, map[string]any{
			"id":          cfg.ID.Hex(),
			"name":        cfg.Name,
			"config_data": cfg.ConfigData,
			"created_at":  cfg.CreatedAt.Format(time.RFC3339),
			"updated_at":  cfg.UpdatedAt.Format(time.RFC3339),
		})
	}
}

func saveConfig(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, user commonauth.User) {
		var input configPayload
		if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный JSON")
			return
		}
		input.Name = strings.TrimSpace(input.Name)
		if input.Name == "" {
			app.Error(w, http.StatusBadRequest, "Название не может быть пустым")
			return
		}
		if len(input.Name) > 100 {
			app.Error(w, http.StatusBadRequest, "Название не должно превышать 100 символов")
			return
		}
		now := time.Now().UTC()
		cfg := savedConfig{
			UserID:     user.ID.Hex(),
			Name:       input.Name,
			ConfigData: input.ConfigData,
			CreatedAt:  now,
			UpdatedAt:  now,
		}
		result, err := store.SavedConfigs.InsertOne(r.Context(), cfg)
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка сохранения конфигурации")
			return
		}
		id := result.InsertedID.(primitive.ObjectID)
		app.JSON(w, http.StatusOK, map[string]any{"success": true, "message": "Конфигурация сохранена", "id": id.Hex(), "name": cfg.Name})
	}
}

func updateConfig(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, user commonauth.User) {
		id, err := primitive.ObjectIDFromHex(r.PathValue("configID"))
		if err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный ID конфигурации")
			return
		}
		var input configPayload
		if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный JSON")
			return
		}
		update := bson.M{"updated_at": time.Now().UTC()}
		if strings.TrimSpace(input.Name) != "" {
			update["name"] = strings.TrimSpace(input.Name)
		}
		if input.ConfigData != nil {
			update["config_data"] = input.ConfigData
		}

		result, err := store.SavedConfigs.UpdateOne(r.Context(), bson.M{"_id": id, "user_id": user.ID.Hex()}, bson.M{"$set": update})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка обновления конфигурации")
			return
		}
		if result.MatchedCount == 0 {
			app.Error(w, http.StatusNotFound, "Конфигурация не найдена")
			return
		}
		name, _ := update["name"].(string)
		app.JSON(w, http.StatusOK, map[string]any{"success": true, "message": "Конфигурация обновлена", "id": id.Hex(), "name": name})
	}
}

func deleteConfig(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, user commonauth.User) {
		id, err := primitive.ObjectIDFromHex(r.PathValue("configID"))
		if err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный ID конфигурации")
			return
		}
		result, err := store.SavedConfigs.DeleteOne(r.Context(), bson.M{"_id": id, "user_id": user.ID.Hex()})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка удаления конфигурации")
			return
		}
		if result.DeletedCount == 0 {
			app.Error(w, http.StatusNotFound, "Конфигурация не найдена")
			return
		}
		app.JSON(w, http.StatusOK, map[string]any{"success": true, "message": "Конфигурация удалена"})
	}
}

func readAll(file multipart.File) ([]byte, error) {
	return io.ReadAll(file)
}
