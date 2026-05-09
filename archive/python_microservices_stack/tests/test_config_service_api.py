import importlib
from datetime import datetime

from bson import ObjectId
from fastapi.testclient import TestClient

from python_microservices import database
from tests.conftest import FakeDB


database.init_db = lambda: None
config_app_module = importlib.import_module("python_microservices.services.config_service.app")


def make_client(fake_db, current_user=None):
    current_user = current_user or {"_id": "user-1", "username": "tester", "is_admin": False}
    config_app_module.app.dependency_overrides[config_app_module.get_db] = lambda: fake_db
    config_app_module.app.dependency_overrides[config_app_module.get_current_user] = lambda: current_user
    return TestClient(config_app_module.app)


def clear_overrides():
    config_app_module.app.dependency_overrides.clear()


def test_save_and_list_configs():
    fake_db = FakeDB()
    client = make_client(fake_db)

    save_response = client.post("/api/configs", json={"name": "Test config", "config_data": {"robotType": "cartesian"}})
    list_response = client.get("/api/configs")

    clear_overrides()
    assert save_response.status_code == 200
    assert save_response.json()["success"] is True
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["name"] == "Test config"


def test_update_config_changes_name_and_payload():
    config_id = ObjectId()
    fake_db = FakeDB(
        saved_configs=[
            {
                "_id": config_id,
                "user_id": "user-1",
                "name": "Old",
                "config_data": {"a": 1},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        ]
    )
    client = make_client(fake_db)

    response = client.put(f"/api/configs/{config_id}", json={"name": "New", "config_data": {"a": 2}})

    clear_overrides()
    assert response.status_code == 200
    updated = fake_db.saved_configs.find_one({"_id": config_id})
    assert updated["name"] == "New"
    assert updated["config_data"] == {"a": 2}


def test_delete_config_removes_owned_document():
    config_id = ObjectId()
    fake_db = FakeDB(
        saved_configs=[
            {
                "_id": config_id,
                "user_id": "user-1",
                "name": "Delete me",
                "config_data": {"a": 1},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        ]
    )
    client = make_client(fake_db)

    response = client.delete(f"/api/configs/{config_id}")

    clear_overrides()
    assert response.status_code == 200
    assert fake_db.saved_configs.items == []


def test_get_config_returns_owned_document():
    config_id = ObjectId()
    fake_db = FakeDB(
        saved_configs=[
            {
                "_id": config_id,
                "user_id": "user-1",
                "name": "Stored",
                "config_data": {"robotType": "scara"},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
        ]
    )
    client = make_client(fake_db)

    response = client.get(f"/api/configs/{config_id}")

    clear_overrides()
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(config_id)
    assert payload["name"] == "Stored"
    assert payload["config_data"]["robotType"] == "scara"
