package mongo

import (
	"context"
	"os"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

type Store struct {
	Client       *mongo.Client
	DB           *mongo.Database
	Users        *mongo.Collection
	SavedConfigs *mongo.Collection
}

func Connect(ctx context.Context) (*Store, error) {
	uri := envDefault("MONGO_URL", "mongodb://localhost:27017")
	dbName := envDefault("MONGO_DB_NAME", "webapp_robot")

	client, err := mongo.Connect(ctx, options.Client().ApplyURI(uri))
	if err != nil {
		return nil, err
	}

	db := client.Database(dbName)
	store := &Store{
		Client:       client,
		DB:           db,
		Users:        db.Collection("users"),
		SavedConfigs: db.Collection("saved_configs"),
	}

	if err := ensureIndexes(ctx, store); err != nil {
		return nil, err
	}
	return store, nil
}

func ensureIndexes(ctx context.Context, store *Store) error {
	idxCtx, cancel := context.WithTimeout(ctx, 10*time.Second)
	defer cancel()

	_, err := store.Users.Indexes().CreateOne(idxCtx, mongo.IndexModel{
		Keys:    bson.D{{Key: "username", Value: 1}},
		Options: options.Index().SetUnique(true).SetName("idx_users_username_unique"),
	})
	if err != nil {
		return err
	}

	_, err = store.SavedConfigs.Indexes().CreateOne(idxCtx, mongo.IndexModel{
		Keys:    bson.D{{Key: "user_id", Value: 1}, {Key: "updated_at", Value: -1}},
		Options: options.Index().SetName("idx_configs_user_updated"),
	})
	return err
}

func envDefault(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}
