import importlib
from datetime import datetime

from bson import ObjectId
from fastapi.testclient import TestClient

from python_microservices import database
from tests.conftest import FakeDB


database.init_db = lambda: None
admin_app_module = importlib.import_module("python_microservices.services.admin_service.app")


def make_client(fake_db, admin_user=None):
    admin_user = admin_user or {"_id": "admin-1", "username": "admin", "is_admin": True}
    admin_app_module.app.dependency_overrides[admin_app_module.get_db] = lambda: fake_db
    admin_app_module.app.dependency_overrides[admin_app_module.require_admin] = lambda: admin_user
    return TestClient(admin_app_module.app)


def clear_overrides():
    admin_app_module.app.dependency_overrides.clear()


def test_admin_get_all_users_includes_config_count():
    fake_db = FakeDB(
        users=[
            {"_id": "u1", "username": "alice", "is_admin": False, "created_at": datetime.utcnow()},
            {"_id": "u2", "username": "bob", "is_admin": False, "created_at": datetime.utcnow()},
        ],
        saved_configs=[
            {"_id": "c1", "user_id": "u1", "name": "cfg", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
        ],
    )
    client = make_client(fake_db)

    response = client.get("/api/admin/users")

    clear_overrides()
    assert response.status_code == 200
    payload = response.json()
    alice = next(item for item in payload if item["username"] == "alice")
    assert alice["configs_count"] == 1


def test_admin_cannot_delete_self():
    admin_id = ObjectId()
    admin_user = {"_id": admin_id, "username": "admin", "is_admin": True}
    fake_db = FakeDB(users=[{"_id": admin_id, "username": "admin", "is_admin": True, "created_at": datetime.utcnow()}])
    client = make_client(fake_db, admin_user=admin_user)

    response = client.delete(f"/api/admin/users/{admin_id}")

    clear_overrides()
    assert response.status_code == 400


def test_admin_toggle_admin_updates_user_role():
    admin_id = ObjectId()
    user_id = ObjectId()
    fake_db = FakeDB(
        users=[
            {"_id": admin_id, "username": "admin", "is_admin": True, "created_at": datetime.utcnow()},
            {"_id": user_id, "username": "alice", "is_admin": False, "created_at": datetime.utcnow()},
        ]
    )
    client = make_client(fake_db, admin_user={"_id": admin_id, "username": "admin", "is_admin": True})

    response = client.put(f"/api/admin/users/{user_id}/toggle-admin")

    clear_overrides()
    assert response.status_code == 200
    assert fake_db.users.find_one({"_id": user_id})["is_admin"] is True
