import datetime as dt
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from pydantic import BaseModel, field_validator

from python_microservices.database import get_db, init_db
from python_microservices.shared.app_factory import create_service_app
from python_microservices.shared.auth_core import get_current_user
from python_microservices.shared.config_files import config_to_frontend_state, decode_upload_file, generate_config_file, parse_config_file


app = create_service_app("Config Service")
init_db()


class SaveConfigRequest(BaseModel):
    name: str
    config_data: dict

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Название не может быть пустым")
        if len(value) > 100:
            raise ValueError("Название не должно превышать 100 символов")
        return value


class UpdateConfigRequest(BaseModel):
    name: Optional[str] = None
    config_data: Optional[dict] = None


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "config", "time": dt.datetime.utcnow().isoformat()}


@app.post("/api/data/upload")
async def upload_config_file(file: UploadFile = File(...)):
    text_content = await decode_upload_file(file)
    config = parse_config_file(text_content)
    return {"success": True, "message": "Файл успешно загружен", "filename": file.filename, "state": config_to_frontend_state(config)}


@app.post("/api/data/download")
async def download_config_file(state: dict):
    file_bytes = generate_config_file(state).encode("cp1251")
    return Response(content=file_bytes, media_type="text/plain; charset=windows-1251", headers={"Content-Disposition": "attachment; filename=robot_config.txt"})


@app.get("/api/configs", response_model=list)
def get_user_configs(current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    configs = list(db.saved_configs.find({"user_id": str(current_user["_id"])}).sort("updated_at", -1))
    return [{"id": str(c["_id"]), "name": c["name"], "created_at": c["created_at"].isoformat(), "updated_at": c["updated_at"].isoformat()} for c in configs]


@app.get("/api/configs/{config_id}")
def get_config(config_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        oid = ObjectId(config_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректный ID конфигурации") from exc

    config = db.saved_configs.find_one({"_id": oid, "user_id": str(current_user["_id"])})
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Конфигурация не найдена")
    return {"id": str(config["_id"]), "name": config["name"], "config_data": config["config_data"], "created_at": config["created_at"].isoformat(), "updated_at": config["updated_at"].isoformat()}


@app.post("/api/configs")
def save_config(data: SaveConfigRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    now = datetime.utcnow()
    config_doc = {"user_id": str(current_user["_id"]), "name": data.name.strip(), "config_data": data.config_data, "created_at": now, "updated_at": now}
    result = db.saved_configs.insert_one(config_doc)
    return {"success": True, "message": "Конфигурация сохранена", "id": str(result.inserted_id), "name": config_doc["name"]}


@app.put("/api/configs/{config_id}")
def update_config(config_id: str, data: UpdateConfigRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        oid = ObjectId(config_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректный ID конфигурации") from exc

    config = db.saved_configs.find_one({"_id": oid, "user_id": str(current_user["_id"])})
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Конфигурация не найдена")

    update_fields = {"updated_at": datetime.utcnow()}
    if data.name is not None:
        update_fields["name"] = data.name.strip()
    if data.config_data is not None:
        update_fields["config_data"] = data.config_data
    db.saved_configs.update_one({"_id": oid}, {"$set": update_fields})
    return {"success": True, "message": "Конфигурация обновлена", "id": config_id, "name": update_fields.get("name", config["name"])}


@app.delete("/api/configs/{config_id}")
def delete_config(config_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    try:
        oid = ObjectId(config_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Некорректный ID конфигурации") from exc

    result = db.saved_configs.delete_one({"_id": oid, "user_id": str(current_user["_id"])})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Конфигурация не найдена")
    return {"success": True, "message": "Конфигурация удалена"}
