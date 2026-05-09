package auth

import (
	"errors"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
	"golang.org/x/crypto/bcrypt"

	mongostore "webapp-go-services/internal/common/mongo"
)

type User struct {
	ID             primitive.ObjectID `bson:"_id,omitempty" json:"id"`
	Username       string             `bson:"username" json:"username"`
	Email          *string            `bson:"email,omitempty" json:"email,omitempty"`
	HashedPassword string             `bson:"hashed_password" json:"-"`
	IsAdmin        bool               `bson:"is_admin" json:"is_admin"`
	CreatedAt      time.Time          `bson:"created_at" json:"created_at"`
}

type Claims struct {
	IsAdmin bool `json:"is_admin,omitempty"`
	jwt.RegisteredClaims
}

func SecretKey() string {
	if value := os.Getenv("SECRET_KEY"); value != "" {
		return value
	}
	return "your-secret-key-change-in-production"
}

func HashPassword(password string) (string, error) {
	hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(hash), err
}

func VerifyPassword(plainPassword, hashedPassword string) bool {
	return bcrypt.CompareHashAndPassword([]byte(hashedPassword), []byte(plainPassword)) == nil
}

func CreateToken(username string, isAdmin bool, ttl time.Duration) (string, error) {
	claims := Claims{
		IsAdmin: isAdmin,
		RegisteredClaims: jwt.RegisteredClaims{
			Subject:   username,
			ExpiresAt: jwt.NewNumericDate(time.Now().Add(ttl)),
			IssuedAt:  jwt.NewNumericDate(time.Now()),
		},
	}
	return jwt.NewWithClaims(jwt.SigningMethodHS256, claims).SignedString([]byte(SecretKey()))
}

func ParseToken(token string) (*Claims, error) {
	parsed, err := jwt.ParseWithClaims(token, &Claims{}, func(_ *jwt.Token) (any, error) {
		return []byte(SecretKey()), nil
	})
	if err != nil {
		return nil, err
	}
	claims, ok := parsed.Claims.(*Claims)
	if !ok || !parsed.Valid || claims.Subject == "" {
		return nil, errors.New("invalid token")
	}
	return claims, nil
}

func BearerToken(r *http.Request) (string, error) {
	header := strings.TrimSpace(r.Header.Get("Authorization"))
	if header == "" {
		return "", errors.New("missing authorization header")
	}
	if !strings.HasPrefix(strings.ToLower(header), "bearer ") {
		return "", errors.New("invalid authorization header")
	}
	return strings.TrimSpace(header[7:]), nil
}

func RequireUser(store *mongostore.Store, next func(http.ResponseWriter, *http.Request, User)) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token, err := BearerToken(r)
		if err != nil {
			http.Error(w, `{"detail":"Необходима авторизация"}`, http.StatusUnauthorized)
			return
		}
		claims, err := ParseToken(token)
		if err != nil {
			http.Error(w, `{"detail":"Неверные учетные данные"}`, http.StatusUnauthorized)
			return
		}

		var user User
		err = store.Users.FindOne(r.Context(), bson.M{"username": claims.Subject}).Decode(&user)
		if err != nil {
			http.Error(w, `{"detail":"Неверные учетные данные"}`, http.StatusUnauthorized)
			return
		}
		next(w, r, user)
	}
}

func RequireAdmin(store *mongostore.Store, next func(http.ResponseWriter, *http.Request, User)) http.HandlerFunc {
	return RequireUser(store, func(w http.ResponseWriter, r *http.Request, user User) {
		if !user.IsAdmin {
			http.Error(w, `{"detail":"Доступ запрещен"}`, http.StatusForbidden)
			return
		}
		next(w, r, user)
	})
}
