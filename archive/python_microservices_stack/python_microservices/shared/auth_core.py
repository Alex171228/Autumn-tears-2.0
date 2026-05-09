import hashlib
import logging
import os
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, field_validator

from python_microservices.database import get_db


security_logger = logging.getLogger("security")
security = HTTPBearer()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
ADMIN_TOKEN_EXPIRE_MINUTES = 30
USERNAME_RE = r"^[a-zA-Zа-яА-ЯёЁ0-9_-]+$"


class BruteForceProtection:
    def __init__(self):
        self.failed_attempts_by_ip: Dict[str, list] = defaultdict(list)
        self.failed_attempts_by_user: Dict[str, list] = defaultdict(list)
        self.global_failed_attempts: list = []
        self.blocked_ips: Dict[str, datetime] = {}
        self.blocked_users: Dict[str, datetime] = {}
        self.MAX_ATTEMPTS_PER_IP = 5
        self.MAX_ATTEMPTS_PER_USER = 3
        self.MAX_GLOBAL_ATTEMPTS = 50
        self.ATTEMPT_WINDOW = 300
        self.BLOCK_DURATION = 900

    def _clean_old_attempts(self, attempts: list) -> list:
        cutoff = datetime.now() - timedelta(seconds=self.ATTEMPT_WINDOW)
        return [a for a in attempts if a > cutoff]

    def _is_blocked(self, blocked_dict: dict, key: str) -> bool:
        if key in blocked_dict:
            if datetime.now() < blocked_dict[key]:
                return True
            del blocked_dict[key]
        return False

    def check_and_record_attempt(self, ip: str, username: str, success: bool, is_admin_attempt: bool = False) -> None:
        now = datetime.now()
        status_str = "SUCCESS" if success else "FAILED"
        admin_str = "[ADMIN]" if is_admin_attempt else ""
        security_logger.info("Login attempt %s: IP=%s, user=%s, status=%s", admin_str, ip, username, status_str)

        if success:
            self.failed_attempts_by_ip[ip] = []
            self.failed_attempts_by_user[username] = []
            return

        self.failed_attempts_by_ip[ip].append(now)
        self.failed_attempts_by_user[username].append(now)
        self.global_failed_attempts.append(now)

        self.failed_attempts_by_ip[ip] = self._clean_old_attempts(self.failed_attempts_by_ip[ip])
        self.failed_attempts_by_user[username] = self._clean_old_attempts(self.failed_attempts_by_user[username])
        self.global_failed_attempts = self._clean_old_attempts(self.global_failed_attempts)

        max_ip = 3 if is_admin_attempt else self.MAX_ATTEMPTS_PER_IP
        max_user = 2 if is_admin_attempt else self.MAX_ATTEMPTS_PER_USER

        if len(self.failed_attempts_by_ip[ip]) >= max_ip:
            self.blocked_ips[ip] = now + timedelta(seconds=self.BLOCK_DURATION)

        if len(self.failed_attempts_by_user[username]) >= max_user:
            self.blocked_users[username] = now + timedelta(seconds=self.BLOCK_DURATION)

    def is_allowed(self, ip: str, username: str = None) -> tuple[bool, str]:
        self.global_failed_attempts = self._clean_old_attempts(self.global_failed_attempts)
        if len(self.global_failed_attempts) >= self.MAX_GLOBAL_ATTEMPTS:
            return False, "Слишком много попыток входа. Попробуйте позже."

        if self._is_blocked(self.blocked_ips, ip):
            remaining = (self.blocked_ips[ip] - datetime.now()).seconds // 60
            return False, f"IP заблокирован. Попробуйте через {remaining + 1} мин."

        if username and self._is_blocked(self.blocked_users, username):
            remaining = (self.blocked_users[username] - datetime.now()).seconds // 60
            return False, f"Аккаунт временно заблокирован. Попробуйте через {remaining + 1} мин."

        return True, ""


class AdminSessionManager:
    def __init__(self):
        self.admin_sessions: Dict[str, dict] = {}
        self.SESSION_TIMEOUT = 1800

    def create_session(self, token: str, ip: str, user_agent: str, username: str) -> str:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.admin_sessions[token_hash] = {
            "ip": ip,
            "user_agent": user_agent,
            "username": username,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
        }
        return token_hash

    def validate_session(self, token: str, ip: str, user_agent: str) -> tuple[bool, str]:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash not in self.admin_sessions:
            return False, "Сессия не найдена"

        session = self.admin_sessions[token_hash]
        if datetime.now() - session["last_activity"] > timedelta(seconds=self.SESSION_TIMEOUT):
            del self.admin_sessions[token_hash]
            return False, "Сессия истекла. Войдите заново."

        if session["ip"] != ip:
            del self.admin_sessions[token_hash]
            return False, "Обнаружена подозрительная активность. Войдите заново."

        session["last_activity"] = datetime.now()
        return True, ""


brute_force_protection = BruteForceProtection()
admin_session_manager = AdminSessionManager()


class UserRegister(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3 or len(value) > 30:
            raise ValueError("Имя пользователя должно содержать от 3 до 30 символов")
        if not re.match(USERNAME_RE, value):
            raise ValueError("Имя пользователя содержит недопустимые символы")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6 or len(value) > 128:
            raise ValueError("Пароль должен содержать от 6 до 128 символов")
        return value


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    is_admin: bool = False


class UserResponse(BaseModel):
    username: str
    email: Optional[str] = None
    is_admin: bool = False


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None or not isinstance(username, str):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")
        if len(username) > 30 or not re.match(USERNAME_RE, username):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные") from exc

    user = db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверные учетные данные")
    return user


def require_admin(current_user: dict = Depends(get_current_user)):
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")
    return current_user


async def require_admin_with_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Недействительный токен") from exc

    user = db.users.find_one({"username": username})
    if not user or not user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    forwarded_for = request.headers.get("x-forwarded-for", "")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else (request.client.host if request.client else "unknown")
    user_agent = request.headers.get("user-agent", "unknown")
    is_valid, error_msg = admin_session_manager.validate_session(token, client_ip, user_agent)
    if not is_valid:
        raise HTTPException(status_code=401, detail=error_msg)
    return user
