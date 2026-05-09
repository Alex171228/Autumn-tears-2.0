import datetime as dt

from bson import ObjectId
from fastapi import Depends, HTTPException, Request

from python_microservices.database import get_db, init_db
from python_microservices.shared.app_factory import create_service_app
from python_microservices.shared.auth_core import require_admin


app = create_service_app("Admin Service")
init_db()


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "admin", "time": dt.datetime.utcnow().isoformat()}


@app.get("/api/admin/users")
def admin_get_all_users(request: Request, admin: dict = Depends(require_admin), db=Depends(get_db)):
    users = list(db.users.find().sort("created_at", -1))
    return [{"id": str(u["_id"]), "username": u["username"], "is_admin": u.get("is_admin", False), "created_at": u["created_at"].isoformat(), "configs_count": db.saved_configs.count_documents({"user_id": str(u["_id"])})} for u in users]


@app.get("/api/admin/users/{user_id}")
def admin_get_user(request: Request, user_id: str, admin: dict = Depends(require_admin), db=Depends(get_db)):
    try:
        oid = ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректный ID пользователя") from exc
    user = db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    configs = list(db.saved_configs.find({"user_id": str(user["_id"])}))
    return {"id": str(user["_id"]), "username": user["username"], "is_admin": user.get("is_admin", False), "created_at": user["created_at"].isoformat(), "configs": [{"id": str(c["_id"]), "name": c["name"], "created_at": c["created_at"].isoformat(), "updated_at": c["updated_at"].isoformat()} for c in configs]}


@app.get("/api/admin/configs")
def admin_get_all_configs(request: Request, admin: dict = Depends(require_admin), db=Depends(get_db)):
    configs = list(db.saved_configs.find().sort("updated_at", -1))
    result = []
    for config in configs:
        owner = db.users.find_one({"_id": ObjectId(config["user_id"])})
        result.append({"id": str(config["_id"]), "name": config["name"], "user_id": config["user_id"], "username": owner["username"] if owner else "unknown", "created_at": config["created_at"].isoformat(), "updated_at": config["updated_at"].isoformat()})
    return result


@app.get("/api/admin/configs/{config_id}")
def admin_get_config(request: Request, config_id: str, admin: dict = Depends(require_admin), db=Depends(get_db)):
    try:
        oid = ObjectId(config_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректный ID конфигурации") from exc
    config = db.saved_configs.find_one({"_id": oid})
    if not config:
        raise HTTPException(status_code=404, detail="Конфигурация не найдена")
    owner = db.users.find_one({"_id": ObjectId(config["user_id"])})
    return {"id": str(config["_id"]), "name": config["name"], "user_id": config["user_id"], "username": owner["username"] if owner else "unknown", "config_data": config["config_data"], "created_at": config["created_at"].isoformat(), "updated_at": config["updated_at"].isoformat()}


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(request: Request, user_id: str, admin: dict = Depends(require_admin), db=Depends(get_db)):
    try:
        oid = ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректный ID пользователя") from exc
    user = db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if str(user["_id"]) == str(admin["_id"]):
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    if user.get("is_admin", False):
        raise HTTPException(status_code=400, detail="Нельзя удалить другого администратора")
    db.saved_configs.delete_many({"user_id": str(user["_id"])})
    db.users.delete_one({"_id": oid})
    return {"success": True, "message": f"Пользователь {user['username']} удалён"}


@app.delete("/api/admin/configs/{config_id}")
def admin_delete_config(request: Request, config_id: str, admin: dict = Depends(require_admin), db=Depends(get_db)):
    try:
        oid = ObjectId(config_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректный ID конфигурации") from exc
    config = db.saved_configs.find_one({"_id": oid})
    if not config:
        raise HTTPException(status_code=404, detail="Конфигурация не найдена")
    owner = db.users.find_one({"_id": ObjectId(config["user_id"])})
    db.saved_configs.delete_one({"_id": oid})
    username = owner["username"] if owner else "unknown"
    return {"success": True, "message": f"Конфигурация '{config['name']}' пользователя {username} удалена"}


@app.put("/api/admin/users/{user_id}/toggle-admin")
def admin_toggle_admin(request: Request, user_id: str, admin: dict = Depends(require_admin), db=Depends(get_db)):
    try:
        oid = ObjectId(user_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректный ID пользователя") from exc
    user = db.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if str(user["_id"]) == str(admin["_id"]):
        raise HTTPException(status_code=400, detail="Нельзя изменить свои права")
    new_is_admin = not user.get("is_admin", False)
    db.users.update_one({"_id": oid}, {"$set": {"is_admin": new_is_admin}})
    return {"success": True, "message": f"Пользователь {user['username']} {'получил' if new_is_admin else 'лишён'} прав администратора", "is_admin": new_is_admin}
