import importlib
from datetime import datetime

from fastapi.testclient import TestClient

from python_microservices import database
from python_microservices.shared import auth_core
from tests.conftest import FakeDB


database.init_db = lambda: None
database.create_admin_user = lambda *args, **kwargs: None
auth_app_module = importlib.import_module("python_microservices.services.auth_service.app")


def make_client(fake_db):
    auth_app_module.app.dependency_overrides[auth_app_module.get_db] = lambda: fake_db
    return TestClient(auth_app_module.app)


def clear_overrides():
    auth_app_module.app.dependency_overrides.clear()


def test_register_creates_user_and_returns_token():
    fake_db = FakeDB()
    client = make_client(fake_db)

    response = client.post("/api/register", json={"username": "newuser", "password": "secret123"})

    clear_overrides()
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "newuser"
    assert payload["token_type"] == "bearer"
    assert fake_db.users.find_one({"username": "newuser"}) is not None


def test_login_returns_admin_flag_for_admin_user():
    fake_db = FakeDB(
        users=[
            {
                "_id": "1",
                "username": "admin",
                "hashed_password": auth_core.hash_password("admin123"),
                "is_admin": True,
                "created_at": datetime.utcnow(),
            }
        ]
    )
    client = make_client(fake_db)

    response = client.post("/api/login", json={"username": "admin", "password": "admin123"})

    clear_overrides()
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "admin"
    assert payload["is_admin"] is True
    assert payload["access_token"]


def test_change_password_updates_hash():
    current_user = {
        "_id": "1",
        "username": "user",
        "hashed_password": auth_core.hash_password("oldpass"),
        "is_admin": False,
    }
    fake_db = FakeDB(users=[current_user])
    client = make_client(fake_db)
    auth_app_module.app.dependency_overrides[auth_app_module.get_current_user] = lambda: current_user

    response = client.post("/api/change-password", json={"current_password": "oldpass", "new_password": "newpass123"})

    clear_overrides()
    assert response.status_code == 200
    updated = fake_db.users.find_one({"_id": "1"})
    assert auth_core.verify_password("newpass123", updated["hashed_password"]) is True


def test_weather_without_api_key_returns_stub():
    fake_db = FakeDB()
    client = make_client(fake_db)
    original = auth_app_module.OPENWEATHER_API_KEY
    auth_app_module.OPENWEATHER_API_KEY = None

    response = client.get("/api/weather")

    auth_app_module.OPENWEATHER_API_KEY = original
    clear_overrides()
    assert response.status_code == 200
    assert response.json()["temp_c"] is None


def test_register_rejects_duplicate_username():
    fake_db = FakeDB(
        users=[
            {
                "_id": "1",
                "username": "existing",
                "hashed_password": auth_core.hash_password("secret123"),
                "is_admin": False,
                "created_at": datetime.utcnow(),
            }
        ]
    )
    client = make_client(fake_db)

    response = client.post("/api/register", json={"username": "existing", "password": "secret123"})

    clear_overrides()
    assert response.status_code == 400
