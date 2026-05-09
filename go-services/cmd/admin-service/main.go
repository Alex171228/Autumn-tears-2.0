package main

import (
	"context"
	"net/http"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"

	"webapp-go-services/internal/common/app"
	commonauth "webapp-go-services/internal/common/auth"
	mongostore "webapp-go-services/internal/common/mongo"
)

type configDoc struct {
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
	mux.HandleFunc("GET /healthz", app.HealthHandler("admin-go"))
	mux.Handle("GET /api/admin/users", commonauth.RequireAdmin(store, getUsers(store)))
	mux.Handle("GET /api/admin/users/{userID}", commonauth.RequireAdmin(store, getUser(store)))
	mux.Handle("DELETE /api/admin/users/{userID}", commonauth.RequireAdmin(store, deleteUser(store)))
	mux.Handle("PUT /api/admin/users/{userID}/toggle-admin", commonauth.RequireAdmin(store, toggleAdmin(store)))
	mux.Handle("GET /api/admin/configs", commonauth.RequireAdmin(store, getConfigs(store)))
	mux.Handle("GET /api/admin/configs/{configID}", commonauth.RequireAdmin(store, getConfig(store)))
	mux.Handle("DELETE /api/admin/configs/{configID}", commonauth.RequireAdmin(store, deleteConfig(store)))

	app.ListenAndServe("admin-go", mux)
}

func getUsers(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, _ commonauth.User) {
		cursor, err := store.Users.Find(r.Context(), bson.M{})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка чтения пользователей")
			return
		}
		defer cursor.Close(r.Context())
		var users []commonauth.User
		if err := cursor.All(r.Context(), &users); err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка чтения пользователей")
			return
		}
		result := make([]map[string]any, 0, len(users))
		for _, user := range users {
			count, _ := store.SavedConfigs.CountDocuments(r.Context(), bson.M{"user_id": user.ID.Hex()})
			result = append(result, map[string]any{
				"id":            user.ID.Hex(),
				"username":      user.Username,
				"is_admin":      user.IsAdmin,
				"created_at":    user.CreatedAt.Format(time.RFC3339),
				"configs_count": count,
			})
		}
		app.JSON(w, http.StatusOK, result)
	}
}

func getUser(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, _ commonauth.User) {
		id, err := primitive.ObjectIDFromHex(r.PathValue("userID"))
		if err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный ID пользователя")
			return
		}
		var user commonauth.User
		if err := store.Users.FindOne(r.Context(), bson.M{"_id": id}).Decode(&user); err != nil {
			app.Error(w, http.StatusNotFound, "Пользователь не найден")
			return
		}
		cursor, err := store.SavedConfigs.Find(r.Context(), bson.M{"user_id": user.ID.Hex()})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка чтения конфигураций")
			return
		}
		defer cursor.Close(r.Context())
		var configs []configDoc
		_ = cursor.All(r.Context(), &configs)
		items := make([]map[string]any, 0, len(configs))
		for _, cfg := range configs {
			items = append(items, map[string]any{
				"id":         cfg.ID.Hex(),
				"name":       cfg.Name,
				"created_at": cfg.CreatedAt.Format(time.RFC3339),
				"updated_at": cfg.UpdatedAt.Format(time.RFC3339),
			})
		}
		app.JSON(w, http.StatusOK, map[string]any{
			"id":         user.ID.Hex(),
			"username":   user.Username,
			"is_admin":   user.IsAdmin,
			"created_at": user.CreatedAt.Format(time.RFC3339),
			"configs":    items,
		})
	}
}

func deleteUser(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, admin commonauth.User) {
		id, err := primitive.ObjectIDFromHex(r.PathValue("userID"))
		if err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный ID пользователя")
			return
		}
		var user commonauth.User
		if err := store.Users.FindOne(r.Context(), bson.M{"_id": id}).Decode(&user); err != nil {
			app.Error(w, http.StatusNotFound, "Пользователь не найден")
			return
		}
		if user.ID == admin.ID {
			app.Error(w, http.StatusBadRequest, "Нельзя удалить самого себя")
			return
		}
		if user.IsAdmin {
			app.Error(w, http.StatusBadRequest, "Нельзя удалить другого администратора")
			return
		}
		_, _ = store.SavedConfigs.DeleteMany(r.Context(), bson.M{"user_id": user.ID.Hex()})
		_, _ = store.Users.DeleteOne(r.Context(), bson.M{"_id": user.ID})
		app.JSON(w, http.StatusOK, map[string]any{"success": true, "message": "Пользователь " + user.Username + " удалён"})
	}
}

func toggleAdmin(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, admin commonauth.User) {
		id, err := primitive.ObjectIDFromHex(r.PathValue("userID"))
		if err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный ID пользователя")
			return
		}
		var user commonauth.User
		if err := store.Users.FindOne(r.Context(), bson.M{"_id": id}).Decode(&user); err != nil {
			app.Error(w, http.StatusNotFound, "Пользователь не найден")
			return
		}
		if user.ID == admin.ID {
			app.Error(w, http.StatusBadRequest, "Нельзя изменить свои права")
			return
		}
		newIsAdmin := !user.IsAdmin
		_, err = store.Users.UpdateByID(r.Context(), user.ID, bson.M{"$set": bson.M{"is_admin": newIsAdmin}})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка обновления прав")
			return
		}
		app.JSON(w, http.StatusOK, map[string]any{"success": true, "message": "Права пользователя обновлены", "is_admin": newIsAdmin})
	}
}

func getConfigs(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, _ commonauth.User) {
		cursor, err := store.SavedConfigs.Find(r.Context(), bson.M{})
		if err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка чтения конфигураций")
			return
		}
		defer cursor.Close(r.Context())
		var configs []configDoc
		if err := cursor.All(r.Context(), &configs); err != nil {
			app.Error(w, http.StatusInternalServerError, "Ошибка чтения конфигураций")
			return
		}
		result := make([]map[string]any, 0, len(configs))
		for _, cfg := range configs {
			username := "unknown"
			if ownerID, err := primitive.ObjectIDFromHex(cfg.UserID); err == nil {
				var owner commonauth.User
				if err := store.Users.FindOne(r.Context(), bson.M{"_id": ownerID}).Decode(&owner); err == nil {
					username = owner.Username
				}
			}
			result = append(result, map[string]any{
				"id":         cfg.ID.Hex(),
				"name":       cfg.Name,
				"user_id":    cfg.UserID,
				"username":   username,
				"created_at": cfg.CreatedAt.Format(time.RFC3339),
				"updated_at": cfg.UpdatedAt.Format(time.RFC3339),
			})
		}
		app.JSON(w, http.StatusOK, result)
	}
}

func getConfig(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, _ commonauth.User) {
		id, err := primitive.ObjectIDFromHex(r.PathValue("configID"))
		if err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный ID конфигурации")
			return
		}
		var cfg configDoc
		if err := store.SavedConfigs.FindOne(r.Context(), bson.M{"_id": id}).Decode(&cfg); err != nil {
			app.Error(w, http.StatusNotFound, "Конфигурация не найдена")
			return
		}
		username := "unknown"
		if ownerID, err := primitive.ObjectIDFromHex(cfg.UserID); err == nil {
			var owner commonauth.User
			if err := store.Users.FindOne(r.Context(), bson.M{"_id": ownerID}).Decode(&owner); err == nil {
				username = owner.Username
			}
		}
		app.JSON(w, http.StatusOK, map[string]any{
			"id":          cfg.ID.Hex(),
			"name":        cfg.Name,
			"user_id":     cfg.UserID,
			"username":    username,
			"config_data": cfg.ConfigData,
			"created_at":  cfg.CreatedAt.Format(time.RFC3339),
			"updated_at":  cfg.UpdatedAt.Format(time.RFC3339),
		})
	}
}

func deleteConfig(store *mongostore.Store) func(http.ResponseWriter, *http.Request, commonauth.User) {
	return func(w http.ResponseWriter, r *http.Request, _ commonauth.User) {
		id, err := primitive.ObjectIDFromHex(r.PathValue("configID"))
		if err != nil {
			app.Error(w, http.StatusBadRequest, "Некорректный ID конфигурации")
			return
		}
		result, err := store.SavedConfigs.DeleteOne(r.Context(), bson.M{"_id": id})
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
