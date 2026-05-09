import datetime as dt
import logging
import os
from datetime import datetime, timedelta

import requests
from fastapi import Depends, HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from python_microservices.database import create_admin_user, get_db, init_db
from python_microservices.shared.app_factory import create_service_app
from python_microservices.shared.auth_core import (
    ADMIN_TOKEN_EXPIRE_MINUTES,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ChangePasswordRequest,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
    admin_session_manager,
    brute_force_protection,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)


logging.basicConfig(level=logging.INFO)
app = create_service_app("Auth Service")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
init_db()
create_admin_user("admin", "admin123")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
DEFAULT_CITY = os.getenv("WEATHER_CITY", "Moscow")
DEFAULT_LANG = "ru"


@app.get("/healthz")
def healthz():
    return {"ok": True, "service": "auth", "time": dt.datetime.utcnow().isoformat()}


@app.post("/api/register", response_model=Token)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserRegister, db=Depends(get_db)):
    username = user_data.username.strip()
    if db.users.find_one({"username": username}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким именем уже существует")

    user_doc = {
        "username": username,
        "email": None,
        "hashed_password": hash_password(user_data.password),
        "is_admin": False,
        "created_at": datetime.utcnow(),
    }
    db.users.insert_one(user_doc)
    access_token = create_access_token(data={"sub": username})
    return {"access_token": access_token, "token_type": "bearer", "username": username, "is_admin": False}


@app.post("/api/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, user_data: UserLogin, db=Depends(get_db)):
    client_ip = get_remote_address(request)
    username = user_data.username.strip() if user_data.username else ""
    is_allowed, block_message = brute_force_protection.is_allowed(client_ip, username)
    if not is_allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=block_message)

    db_user = db.users.find_one({"username": username})
    if not db_user or not verify_password(user_data.password, db_user["hashed_password"]):
        brute_force_protection.check_and_record_attempt(client_ip, username, False, is_admin_attempt=(db_user or {}).get("is_admin", False))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверное имя пользователя или пароль")

    brute_force_protection.check_and_record_attempt(client_ip, username, True)
    is_admin = db_user.get("is_admin", False)
    expire_minutes = ADMIN_TOKEN_EXPIRE_MINUTES if is_admin else ACCESS_TOKEN_EXPIRE_MINUTES
    access_token = create_access_token(
        data={"sub": db_user["username"], "is_admin": is_admin},
        expires_delta=timedelta(minutes=expire_minutes),
    )
    if is_admin:
        admin_session_manager.create_session(access_token, client_ip, request.headers.get("user-agent", "unknown"), username)

    return {"access_token": access_token, "token_type": "bearer", "username": db_user["username"], "is_admin": is_admin}


@app.get("/api/me", response_model=UserResponse)
def get_current_user_info(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["username"], "email": current_user.get("email"), "is_admin": current_user.get("is_admin", False)}


@app.get("/api/weather")
def api_weather(city: str = DEFAULT_CITY):
    if not OPENWEATHER_API_KEY:
        return {"city": city, "temp_c": None, "description": "NO OPENWEATHER_API_KEY in .env", "icon_url": None}

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang={DEFAULT_LANG}"
    )
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        icon = data["weather"][0]["icon"] if data.get("weather") else None
        return {
            "city": city,
            "temp_c": data.get("main", {}).get("temp"),
            "description": data.get("weather", [{}])[0].get("description"),
            "icon_url": f"https://openweathermap.org/img/wn/{icon}@2x.png" if icon else None,
        }
    except Exception as exc:
        return {"city": city, "temp_c": None, "description": f"Error: {exc}", "icon_url": None}


@app.post("/api/change-password")
def change_password(request: Request, data: ChangePasswordRequest, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    if not verify_password(data.current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный текущий пароль")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Новый пароль должен содержать минимум 6 символов")
    if data.current_password == data.new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Новый пароль должен отличаться от текущего")

    db.users.update_one({"_id": current_user["_id"]}, {"$set": {"hashed_password": hash_password(data.new_password)}})
    return {"success": True, "message": "Пароль успешно изменён"}
