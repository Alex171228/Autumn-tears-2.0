"""
Модуль работы с базой данных MongoDB.
Замена SQLAlchemy/SQLite на pymongo.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime
import os
import bcrypt

# Подключение к MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "webapp_robot"

_client = None
_db = None


def get_client():
    """Получить клиент MongoDB (lazy singleton)"""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URL)
    return _client


def get_database():
    """Получить объект базы данных"""
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db


def get_db():
    """Dependency для FastAPI — возвращает объект базы pymongo"""
    return get_database()


def init_db():
    """Инициализация базы данных: создание индексов"""
    db = get_database()

    # Коллекция users: уникальный индекс по username
    db.users.create_index(
        [("username", ASCENDING)],
        unique=True,
        name="idx_users_username_unique"
    )

    # Коллекция saved_configs: индекс по user_id + сортировка по updated_at
    db.saved_configs.create_index(
        [("user_id", ASCENDING), ("updated_at", DESCENDING)],
        name="idx_configs_user_updated"
    )

    print("MongoDB: индексы созданы")


def create_admin_user(username: str = "admin", password: str = "admin123"):
    """Создаёт пользователя-администратора если его нет (upsert)"""
    db = get_database()
    try:
        existing = db.users.find_one({"username": username})

        if existing:
            if not existing.get("is_admin", False):
                db.users.update_one(
                    {"_id": existing["_id"]},
                    {"$set": {"is_admin": True}}
                )
                print(f"Пользователь '{username}' получил права администратора")
            else:
                print(f"Администратор '{username}' уже существует")
            return existing

        # Создаём нового админа
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        admin_doc = {
            "username": username,
            "email": None,
            "hashed_password": hashed.decode('utf-8'),
            "is_admin": True,
            "created_at": datetime.utcnow(),
        }
        result = db.users.insert_one(admin_doc)
        admin_doc["_id"] = result.inserted_id
        print(f"Создан администратор: {username} (пароль: {password})")
        print("ВАЖНО: Смените пароль администратора после первого входа!")
        return admin_doc

    except DuplicateKeyError:
        print(f"Администратор '{username}' уже существует (concurrent create)")
        return db.users.find_one({"username": username})
    except Exception as e:
        print(f"Ошибка создания администратора: {e}")
        return None
