import os
import datetime as dt
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import secrets
import logging

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from typing import Optional, Dict
import re
import requests
import bcrypt
from jose import JWTError, jwt
from dotenv import load_dotenv

from database import init_db, get_db, User, SavedConfig, create_admin_user
import json

# Настройка логирования безопасности
logging.basicConfig(level=logging.INFO)
security_logger = logging.getLogger("security")

# Загружаем .env
load_dotenv()

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
DEFAULT_CITY = os.getenv("WEATHER_CITY", "Moscow")
DEFAULT_LANG = "ru"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней
ADMIN_TOKEN_EXPIRE_MINUTES = 30  # Админ токен живёт только 30 минут

# =====================================================
# СИСТЕМА ЗАЩИТЫ ОТ БРУТФОРСА
# =====================================================

class BruteForceProtection:
    """Защита от брутфорса с разных IP"""
    
    def __init__(self):
        # Неудачные попытки по IP
        self.failed_attempts_by_ip: Dict[str, list] = defaultdict(list)
        # Неудачные попытки по username
        self.failed_attempts_by_user: Dict[str, list] = defaultdict(list)
        # Глобальный счётчик (защита от распределённых атак)
        self.global_failed_attempts: list = []
        # Заблокированные IP
        self.blocked_ips: Dict[str, datetime] = {}
        # Заблокированные пользователи
        self.blocked_users: Dict[str, datetime] = {}
        
        # Настройки
        self.MAX_ATTEMPTS_PER_IP = 5  # Макс попыток с одного IP за период
        self.MAX_ATTEMPTS_PER_USER = 3  # Макс попыток для одного пользователя
        self.MAX_GLOBAL_ATTEMPTS = 50  # Макс глобальных попыток (защита от DDoS)
        self.ATTEMPT_WINDOW = 300  # Окно в секундах (5 минут)
        self.BLOCK_DURATION = 900  # Блокировка на 15 минут
        self.GLOBAL_BLOCK_DURATION = 60  # Глобальная блокировка на 1 минуту
    
    def _clean_old_attempts(self, attempts: list) -> list:
        """Удаляет устаревшие попытки"""
        cutoff = datetime.now() - timedelta(seconds=self.ATTEMPT_WINDOW)
        return [a for a in attempts if a > cutoff]
    
    def _is_blocked(self, blocked_dict: dict, key: str) -> bool:
        """Проверяет заблокирован ли ключ"""
        if key in blocked_dict:
            if datetime.now() < blocked_dict[key]:
                return True
            else:
                del blocked_dict[key]
        return False
    
    def check_and_record_attempt(self, ip: str, username: str, success: bool, is_admin_attempt: bool = False) -> None:
        """Записывает попытку входа и проверяет блокировки"""
        now = datetime.now()
        
        # Логируем попытку
        status_str = "SUCCESS" if success else "FAILED"
        admin_str = "[ADMIN]" if is_admin_attempt else ""
        security_logger.info(f"Login attempt {admin_str}: IP={ip}, user={username}, status={status_str}")
        
        if success:
            # При успешном входе очищаем счётчики
            self.failed_attempts_by_ip[ip] = []
            self.failed_attempts_by_user[username] = []
            return
        
        # Записываем неудачную попытку
        self.failed_attempts_by_ip[ip].append(now)
        self.failed_attempts_by_user[username].append(now)
        self.global_failed_attempts.append(now)
        
        # Очищаем старые
        self.failed_attempts_by_ip[ip] = self._clean_old_attempts(self.failed_attempts_by_ip[ip])
        self.failed_attempts_by_user[username] = self._clean_old_attempts(self.failed_attempts_by_user[username])
        self.global_failed_attempts = self._clean_old_attempts(self.global_failed_attempts)
        
        # Для админских попыток - более строгие ограничения
        max_ip = 3 if is_admin_attempt else self.MAX_ATTEMPTS_PER_IP
        max_user = 2 if is_admin_attempt else self.MAX_ATTEMPTS_PER_USER
        
        # Проверяем превышение лимитов
        if len(self.failed_attempts_by_ip[ip]) >= max_ip:
            block_until = now + timedelta(seconds=self.BLOCK_DURATION)
            self.blocked_ips[ip] = block_until
            security_logger.warning(f"IP BLOCKED: {ip} until {block_until}")
        
        if len(self.failed_attempts_by_user[username]) >= max_user:
            block_until = now + timedelta(seconds=self.BLOCK_DURATION)
            self.blocked_users[username] = block_until
            security_logger.warning(f"USER BLOCKED: {username} until {block_until}")
    
    def is_allowed(self, ip: str, username: str = None) -> tuple[bool, str]:
        """Проверяет разрешён ли доступ"""
        # Проверяем глобальную блокировку (защита от DDoS)
        self.global_failed_attempts = self._clean_old_attempts(self.global_failed_attempts)
        if len(self.global_failed_attempts) >= self.MAX_GLOBAL_ATTEMPTS:
            return False, "Слишком много попыток входа. Попробуйте позже."
        
        # Проверяем блокировку IP
        if self._is_blocked(self.blocked_ips, ip):
            remaining = (self.blocked_ips[ip] - datetime.now()).seconds // 60
            return False, f"IP заблокирован. Попробуйте через {remaining + 1} мин."
        
        # Проверяем блокировку пользователя
        if username and self._is_blocked(self.blocked_users, username):
            remaining = (self.blocked_users[username] - datetime.now()).seconds // 60
            return False, f"Аккаунт временно заблокирован. Попробуйте через {remaining + 1} мин."
        
        return True, ""

# Глобальный экземпляр защиты
brute_force_protection = BruteForceProtection()


# =====================================================
# ЗАЩИТА АДМИН-ПАНЕЛИ
# =====================================================

class AdminSessionManager:
    """Управление сессиями администратора"""
    
    def __init__(self):
        # Активные админ-сессии: token_hash -> {ip, user_agent, created_at, last_activity}
        self.admin_sessions: Dict[str, dict] = {}
        self.SESSION_TIMEOUT = 1800  # 30 минут неактивности
    
    def create_session(self, token: str, ip: str, user_agent: str, username: str) -> str:
        """Создаёт админ-сессию"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.admin_sessions[token_hash] = {
            "ip": ip,
            "user_agent": user_agent,
            "username": username,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        security_logger.info(f"Admin session created: user={username}, IP={ip}")
        return token_hash
    
    def validate_session(self, token: str, ip: str, user_agent: str) -> tuple[bool, str]:
        """Проверяет валидность админ-сессии"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        if token_hash not in self.admin_sessions:
            return False, "Сессия не найдена"
        
        session = self.admin_sessions[token_hash]
        
        # Проверяем timeout
        if datetime.now() - session["last_activity"] > timedelta(seconds=self.SESSION_TIMEOUT):
            del self.admin_sessions[token_hash]
            security_logger.warning(f"Admin session expired: user={session['username']}")
            return False, "Сессия истекла. Войдите заново."
        
        # Проверяем IP (защита от кражи токена)
        if session["ip"] != ip:
            security_logger.warning(
                f"Admin session IP mismatch: user={session['username']}, "
                f"expected={session['ip']}, got={ip}"
            )
            del self.admin_sessions[token_hash]
            return False, "Обнаружена подозрительная активность. Войдите заново."
        
        # Обновляем время активности
        session["last_activity"] = datetime.now()
        return True, ""
    
    def invalidate_session(self, token: str):
        """Удаляет сессию"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in self.admin_sessions:
            session = self.admin_sessions[token_hash]
            security_logger.info(f"Admin session invalidated: user={session['username']}")
            del self.admin_sessions[token_hash]

# Глобальный менеджер админ-сессий
admin_session_manager = AdminSessionManager()


app = FastAPI(title="PyQt → Web UI")

# Rate limiting для защиты от брутфорса
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware для добавления заголовков кэширования
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Определяем тип контента для настройки кэширования
        path = request.url.path
        
        # Статические файлы (JS, CSS, изображения) - кэшируем надолго
        if path.startswith("/static/") or path.endswith((".js", ".css", ".png", ".jpg", ".ico", ".svg", ".woff", ".woff2")):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        # API endpoints - не кэшируем (данные динамические)
        elif path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        # HTML страницы - короткое кэширование с проверкой
        else:
            response.headers["Cache-Control"] = "public, max-age=3600, must-revalidate"
        
        return response

app.add_middleware(CacheControlMiddleware)


os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация БД при запуске
init_db()

# Создаём администратора при первом запуске
# Логин: admin, Пароль: admin123 (СМЕНИТЕ ПОСЛЕ ПЕРВОГО ВХОДА!)
create_admin_user("admin", "admin123")

# Security
security = HTTPBearer()


# Pydantic модели
class UserRegister(BaseModel):
    username: str
    password: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Имя пользователя не может быть пустым')
        v = v.strip()
        if len(v) < 3:
            raise ValueError('Имя пользователя должно содержать не менее 3 символов')
        if len(v) > 30:
            raise ValueError('Имя пользователя не должно превышать 30 символов')
        # Разрешаем только буквы (русские и английские), цифры, дефисы и подчеркивания
        if not re.match(r'^[a-zA-Zа-яА-ЯёЁ0-9_-]+$', v):
            raise ValueError('Имя пользователя может содержать только буквы, цифры, дефисы и подчеркивания')
        return v
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if not v or len(v) < 6:
            raise ValueError('Пароль должен содержать не менее 6 символов')
        if len(v) > 128:
            raise ValueError('Пароль не должен превышать 128 символов')
        return v


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
    email: str = None
    is_admin: bool = False


# Утилиты для работы с паролями и токенами
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Получить текущего пользователя из JWT токена"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None or not isinstance(username, str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
        # Валидация имени пользователя из токена
        if len(username) > 30 or not re.match(r'^[a-zA-Zа-яА-ЯёЁ0-9_-]+$', username):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверные учетные данные"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    # Используем ORM для защиты от SQL инъекций
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные"
        )
    return user


@app.get("/healthz")
def healthz():
    return {"ok": True, "time": dt.datetime.utcnow().isoformat()}


@app.post("/api/register", response_model=Token)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserRegister, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    try:
        # Валидация уже выполнена через Pydantic validators
        username = user_data.username.strip()
        
        # Дополнительная проверка на SQL инъекции (хотя SQLAlchemy уже защищает)
        # Используем параметризованные запросы через ORM
        
        # Проверяем, существует ли пользователь (используем ORM для защиты от SQL инъекций)
        db_user = db.query(User).filter(User.username == username).first()
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким именем уже существует"
            )
        
        # Хешируем пароль
        hashed_password = hash_password(user_data.password)
        
        # Создаем пользователя (без email)
        db_user = User(
            username=username,
            email=None,  # Email больше не используется
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Создаем токен
        access_token = create_access_token(data={"sub": db_user.username})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": db_user.username,
            "is_admin": db_user.is_admin
        }
    except HTTPException:
        raise
    except Exception as e:
        # Логируем ошибку для отладки (но не раскрываем детали пользователю)
        import traceback
        print(f"Ошибка при регистрации: {e}")
        print(traceback.format_exc())
        # Не раскрываем детали ошибки для безопасности
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Произошла ошибка при регистрации. Попробуйте позже."
        )


@app.post("/api/login", response_model=Token)
@limiter.limit("10/minute")
def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    """Вход пользователя"""
    client_ip = get_remote_address(request)
    username = user_data.username.strip() if user_data.username else ""
    
    # Проверяем блокировки (защита от брутфорса)
    is_allowed, block_message = brute_force_protection.is_allowed(client_ip, username)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=block_message
        )
    
    # Валидация входных данных
    if not username or len(username) < 3 or len(username) > 30:
        brute_force_protection.check_and_record_attempt(client_ip, username, False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    # Находим пользователя (используем ORM для защиты от SQL инъекций)
    db_user = db.query(User).filter(User.username == username).first()
    if not db_user:
        brute_force_protection.check_and_record_attempt(client_ip, username, False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    # Проверяем пароль (постоянное время выполнения для защиты от timing attacks)
    if not verify_password(user_data.password, db_user.hashed_password):
        # Для админа - более строгая защита
        brute_force_protection.check_and_record_attempt(
            client_ip, username, False, is_admin_attempt=db_user.is_admin
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    # Успешный вход
    brute_force_protection.check_and_record_attempt(client_ip, username, True)
    
    # Создаем токен (для админа - короче срок действия)
    expire_minutes = ADMIN_TOKEN_EXPIRE_MINUTES if db_user.is_admin else ACCESS_TOKEN_EXPIRE_MINUTES
    access_token = create_access_token(
        data={"sub": db_user.username, "is_admin": db_user.is_admin},
        expires_delta=timedelta(minutes=expire_minutes)
    )
    
    # Для админа создаём сессию с привязкой к IP
    if db_user.is_admin:
        user_agent = request.headers.get("user-agent", "unknown")
        admin_session_manager.create_session(access_token, client_ip, user_agent, username)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": db_user.username,
        "is_admin": db_user.is_admin
    }


@app.get("/api/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return {
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }


@app.get("/api/weather")
def api_weather(city: str = DEFAULT_CITY):
    """Простой аналог WeatherWidget: отдать погоду."""
    if not OPENWEATHER_API_KEY:
        return {
            "city": city,
            "temp_c": None,
            "description": "NO OPENWEATHER_API_KEY in .env",
            "icon_url": None,
        }

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={OPENWEATHER_API_KEY}&units=metric&lang={DEFAULT_LANG}"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return {
            "city": city,
            "temp_c": None,
            "description": f"Error: {e}",
            "icon_url": None,
        }

    data = r.json()
    temp_c = data.get("main", {}).get("temp")
    desc = (data.get("weather") or [{}])[0].get("description")
    icon = (data.get("weather") or [{}])[0].get("icon")
    icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png" if icon else None

    return {
        "city": data.get("name", city),
        "temp_c": temp_c,
        "description": desc,
        "icon_url": icon_url,
    }


# =====================================================
# API для расчёта траекторий роботов
# =====================================================

from trajectory_calculator import TrajectoryCalculator, WorkspaceCalculator, RobotState
from models import (
    RobotType, ControlType, PlotType,
    FullRobotConfig, CyclogramRequest, PIDRequest, MotorParamsRequest,
    CartesianLimitsRequest, CartesianParamsRequest,
    ScaraLimitsRequest, ScaraParamsRequest,
    CylindricalLimitsRequest, CylindricalParamsRequest,
    ColerLimitsRequest, ColerParamsRequest,
    LineContourRequest, CircleContourRequest, SplineRequest,
    TrajectoryResult, PlotResponse, WorkspaceResponse, StatusResponse,
    RobotStateResponse, QualityMetrics, AllDataResponse,
    TrajectoryData, ElectricalData, MechanicalData
)

# Глобальное хранилище калькуляторов для сессий (в продакшене использовать Redis)
robot_calculators: dict = {}


def get_calculator(session_id: str = "default") -> TrajectoryCalculator:
    """Получить или создать калькулятор для сессии"""
    if session_id not in robot_calculators:
        robot_calculators[session_id] = TrajectoryCalculator()
    return robot_calculators[session_id]


@app.post("/api/robot/configure", response_model=StatusResponse)
def configure_robot(config: FullRobotConfig, session_id: str = "default"):
    """Полная конфигурация робота одним запросом"""
    try:
        calc = get_calculator(session_id)
        
        # Обновляем состояние
        calc.state.robot_type = config.robot_type.value
        calc.state.type_of_control = config.type_of_control.value
        calc.state.spline = config.spline
        calc.state.num_splain_dots = config.num_splain_dots
        
        # ПИД
        calc.state.Kp = config.Kp
        calc.state.Ki = config.Ki
        calc.state.Kd = config.Kd
        
        # Циклограмма
        if config.t:
            calc.state.t = config.t
            calc.state.q1 = config.q1
            calc.state.q2 = config.q2
            calc.state.q3 = config.q3 or [0] * len(config.t)
            calc.state.q4 = config.q4 or [0] * len(config.t)
        
        # Двигатели
        calc.state.J = config.J
        calc.state.T_e = config.T_e
        calc.state.Umax = config.Umax
        calc.state.Fi = config.Fi
        calc.state.Ce = config.Ce
        calc.state.Ra = config.Ra
        calc.state.Cm = config.Cm
        
        # Декартовый
        calc.state.x_min = config.x_min
        calc.state.x_max = config.x_max
        calc.state.y_min = config.y_min
        calc.state.y_max = config.y_max
        calc.state.z_min = config.z_min
        calc.state.z_max = config.z_max
        calc.state.massd_1 = config.massd_1
        calc.state.massd_2 = config.massd_2
        calc.state.massd_3 = config.massd_3
        calc.state.momentd_1 = config.momentd_1
        
        # SCARA
        calc.state.q1s_min = config.q1s_min
        calc.state.q1s_max = config.q1s_max
        calc.state.q2s_min = config.q2s_min
        calc.state.q2s_max = config.q2s_max
        calc.state.q3s_min = config.q3s_min
        calc.state.q3s_max = config.q3s_max
        calc.state.zs_min = config.zs_min
        calc.state.zs_max = config.zs_max
        calc.state.moment_1 = config.moment_1
        calc.state.moment_2 = config.moment_2
        calc.state.moment_3 = config.moment_3
        calc.state.length_1 = config.length_1
        calc.state.length_2 = config.length_2
        calc.state.distance = config.distance
        calc.state.masss_2 = config.masss_2
        calc.state.masss_3 = config.masss_3
        
        # Цилиндрический
        calc.state.q1c_min = config.q1c_min
        calc.state.q1c_max = config.q1c_max
        calc.state.a2c_min = config.a2c_min
        calc.state.a2c_max = config.a2c_max
        calc.state.q3c_min = config.q3c_min
        calc.state.q3c_max = config.q3c_max
        calc.state.zc_min = config.zc_min
        calc.state.zc_max = config.zc_max
        calc.state.momentc_1 = config.momentc_1
        calc.state.momentc_2 = config.momentc_2
        calc.state.momentc_3 = config.momentc_3
        calc.state.lengthc_1 = config.lengthc_1
        calc.state.lengthc_2 = config.lengthc_2
        calc.state.distancec = config.distancec
        calc.state.massc_2 = config.massc_2
        calc.state.massc_3 = config.massc_3
        
        # Колер
        calc.state.q1col_min = config.q1col_min
        calc.state.q1col_max = config.q1col_max
        calc.state.a2col_min = config.a2col_min
        calc.state.a2col_max = config.a2col_max
        calc.state.q3col_min = config.q3col_min
        calc.state.q3col_max = config.q3col_max
        calc.state.zcol_min = config.zcol_min
        calc.state.zcol_max = config.zcol_max
        calc.state.momentcol_1 = config.momentcol_1
        calc.state.momentcol_2 = config.momentcol_2
        calc.state.momentcol_3 = config.momentcol_3
        calc.state.lengthcol_1 = config.lengthcol_1
        calc.state.lengthcol_2 = config.lengthcol_2
        calc.state.distancecol = config.distancecol
        calc.state.masscol_2 = config.masscol_2
        calc.state.masscol_3 = config.masscol_3
        
        return {"success": True, "message": "Робот успешно сконфигурирован"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/robot/type", response_model=StatusResponse)
def set_robot_type(robot_type: RobotType, session_id: str = "default"):
    """Установить тип робота"""
    calc = get_calculator(session_id)
    calc.state.robot_type = robot_type.value
    return {"success": True, "message": f"Тип робота установлен: {robot_type.value}"}


@app.post("/api/robot/cyclogram", response_model=StatusResponse)
def set_cyclogram(data: CyclogramRequest, session_id: str = "default"):
    """Установить циклограмму"""
    calc = get_calculator(session_id)
    calc.state.t = data.t
    calc.state.q1 = data.q1
    calc.state.q2 = data.q2
    calc.state.q3 = data.q3 or [0] * len(data.t)
    calc.state.q4 = data.q4 or [0] * len(data.t)
    calc.state.type_of_control = data.type_of_control.value
    return {"success": True, "message": f"Циклограмма установлена ({len(data.t)} точек)"}


@app.post("/api/robot/pid", response_model=StatusResponse)
def set_pid(data: PIDRequest, session_id: str = "default"):
    """Установить параметры ПИД-регулятора"""
    calc = get_calculator(session_id)
    calc.state.Kp = data.Kp
    calc.state.Ki = data.Ki
    calc.state.Kd = data.Kd
    return {"success": True, "message": "Параметры ПИД установлены"}


@app.post("/api/robot/motors", response_model=StatusResponse)
def set_motor_params(data: MotorParamsRequest, session_id: str = "default"):
    """Установить параметры двигателей"""
    calc = get_calculator(session_id)
    calc.state.J = data.J
    calc.state.T_e = data.T_e
    calc.state.Umax = data.Umax
    calc.state.Fi = data.Fi
    calc.state.Ce = data.Ce
    calc.state.Ra = data.Ra
    calc.state.Cm = data.Cm
    return {"success": True, "message": "Параметры двигателей установлены"}


@app.post("/api/robot/cartesian/limits", response_model=StatusResponse)
def set_cartesian_limits(data: CartesianLimitsRequest, session_id: str = "default"):
    """Установить ограничения декартового робота"""
    calc = get_calculator(session_id)
    calc.state.x_min = data.x_min
    calc.state.x_max = data.x_max
    calc.state.y_min = data.y_min
    calc.state.y_max = data.y_max
    calc.state.z_min = data.z_min
    calc.state.z_max = data.z_max
    calc.state.q_min = data.q_min
    calc.state.q_max = data.q_max
    return {"success": True, "message": "Ограничения декартового робота установлены"}


@app.post("/api/robot/cartesian/params", response_model=StatusResponse)
def set_cartesian_params(data: CartesianParamsRequest, session_id: str = "default"):
    """Установить параметры декартового робота"""
    calc = get_calculator(session_id)
    calc.state.massd_1 = data.massd_1
    calc.state.massd_2 = data.massd_2
    calc.state.massd_3 = data.massd_3
    calc.state.momentd_1 = data.momentd_1
    return {"success": True, "message": "Параметры декартового робота установлены"}


@app.post("/api/robot/scara/limits", response_model=StatusResponse)
def set_scara_limits(data: ScaraLimitsRequest, session_id: str = "default"):
    """Установить ограничения SCARA робота"""
    calc = get_calculator(session_id)
    calc.state.q1s_min = data.q1s_min
    calc.state.q1s_max = data.q1s_max
    calc.state.q2s_min = data.q2s_min
    calc.state.q2s_max = data.q2s_max
    calc.state.q3s_min = data.q3s_min
    calc.state.q3s_max = data.q3s_max
    calc.state.zs_min = data.zs_min
    calc.state.zs_max = data.zs_max
    return {"success": True, "message": "Ограничения SCARA робота установлены"}


@app.post("/api/robot/scara/params", response_model=StatusResponse)
def set_scara_params(data: ScaraParamsRequest, session_id: str = "default"):
    """Установить параметры SCARA робота"""
    calc = get_calculator(session_id)
    calc.state.moment_1 = data.moment_1
    calc.state.moment_2 = data.moment_2
    calc.state.moment_3 = data.moment_3
    calc.state.length_1 = data.length_1
    calc.state.length_2 = data.length_2
    calc.state.distance = data.distance
    calc.state.masss_2 = data.masss_2
    calc.state.masss_3 = data.masss_3
    return {"success": True, "message": "Параметры SCARA робота установлены"}


@app.post("/api/robot/cylindrical/limits", response_model=StatusResponse)
def set_cylindrical_limits(data: CylindricalLimitsRequest, session_id: str = "default"):
    """Установить ограничения цилиндрического робота"""
    calc = get_calculator(session_id)
    calc.state.q1c_min = data.q1c_min
    calc.state.q1c_max = data.q1c_max
    calc.state.a2c_min = data.a2c_min
    calc.state.a2c_max = data.a2c_max
    calc.state.q3c_min = data.q3c_min
    calc.state.q3c_max = data.q3c_max
    calc.state.zc_min = data.zc_min
    calc.state.zc_max = data.zc_max
    return {"success": True, "message": "Ограничения цилиндрического робота установлены"}


@app.post("/api/robot/cylindrical/params", response_model=StatusResponse)
def set_cylindrical_params(data: CylindricalParamsRequest, session_id: str = "default"):
    """Установить параметры цилиндрического робота"""
    calc = get_calculator(session_id)
    calc.state.momentc_1 = data.momentc_1
    calc.state.momentc_2 = data.momentc_2
    calc.state.momentc_3 = data.momentc_3
    calc.state.lengthc_1 = data.lengthc_1
    calc.state.lengthc_2 = data.lengthc_2
    calc.state.distancec = data.distancec
    calc.state.massc_2 = data.massc_2
    calc.state.massc_3 = data.massc_3
    return {"success": True, "message": "Параметры цилиндрического робота установлены"}


@app.post("/api/robot/coler/limits", response_model=StatusResponse)
def set_coler_limits(data: ColerLimitsRequest, session_id: str = "default"):
    """Установить ограничения робота Колер"""
    calc = get_calculator(session_id)
    calc.state.q1col_min = data.q1col_min
    calc.state.q1col_max = data.q1col_max
    calc.state.a2col_min = data.a2col_min
    calc.state.a2col_max = data.a2col_max
    calc.state.q3col_min = data.q3col_min
    calc.state.q3col_max = data.q3col_max
    calc.state.zcol_min = data.zcol_min
    calc.state.zcol_max = data.zcol_max
    return {"success": True, "message": "Ограничения робота Колер установлены"}


@app.post("/api/robot/coler/params", response_model=StatusResponse)
def set_coler_params(data: ColerParamsRequest, session_id: str = "default"):
    """Установить параметры робота Колер"""
    calc = get_calculator(session_id)
    calc.state.momentcol_1 = data.momentcol_1
    calc.state.momentcol_2 = data.momentcol_2
    calc.state.momentcol_3 = data.momentcol_3
    calc.state.lengthcol_1 = data.lengthcol_1
    calc.state.lengthcol_2 = data.lengthcol_2
    calc.state.distancecol = data.distancecol
    calc.state.masscol_2 = data.masscol_2
    calc.state.masscol_3 = data.masscol_3
    return {"success": True, "message": "Параметры робота Колер установлены"}


@app.post("/api/robot/contour/line", response_model=StatusResponse)
def set_line_contour(data: LineContourRequest, session_id: str = "default"):
    """Установить линейный контур для контурного управления"""
    calc = get_calculator(session_id)
    calc.state.type_of_control = "Контурное"
    calc.state.line_x1 = data.x1
    calc.state.line_x2 = data.x2
    calc.state.line_y1 = data.y1
    calc.state.line_y2 = data.y2
    calc.state.line_speed = data.speed
    
    # Создаём контур
    calc.create_contour_line(data.x1, data.x2, data.y1, data.y2)
    calc.reverse_coordinate_transform()
    
    return {"success": True, "message": "Линейный контур установлен"}


@app.post("/api/robot/contour/circle", response_model=StatusResponse)
def set_circle_contour(data: CircleContourRequest, session_id: str = "default"):
    """Установить круговой контур для контурного управления"""
    calc = get_calculator(session_id)
    calc.state.type_of_control = "Контурное"
    calc.state.circle_x = data.x
    calc.state.circle_y = data.y
    calc.state.circle_radius = data.radius
    calc.state.circle_speed = data.speed
    
    # Создаём контур
    calc.create_contour_circle(data.x, data.y, data.radius)
    calc.reverse_coordinate_transform()
    
    return {"success": True, "message": "Круговой контур установлен"}


@app.post("/api/robot/spline", response_model=StatusResponse)
def set_spline(data: SplineRequest, session_id: str = "default"):
    """Включить/выключить сплайн-интерполяцию"""
    calc = get_calculator(session_id)
    calc.state.spline = data.enabled
    calc.state.num_splain_dots = data.num_dots
    return {"success": True, "message": f"Сплайн {'включен' if data.enabled else 'выключен'}"}


@app.get("/api/robot/state", response_model=RobotStateResponse)
def get_robot_state(session_id: str = "default"):
    """Получить текущее состояние робота"""
    calc = get_calculator(session_id)
    s = calc.state
    return {
        "robot_type": s.robot_type,
        "type_of_control": s.type_of_control,
        "spline": s.spline,
        "has_cyclogram": len(s.t) > 0 and any(t > 0 for t in s.t),
        "cyclogram_points": len(s.t),
        "pid_configured": any(k > 0 for k in s.Kp + s.Ki + s.Kd),
        "motors_configured": any(j > 0 for j in s.J),
    }


@app.post("/api/robot/calculate")
def calculate_trajectory(session_id: str = "default"):
    """Рассчитать траекторию"""
    try:
        calc = get_calculator(session_id)
        
        # Выполняем расчёт
        calc.calculate_trajectory()
        
        # Преобразование координат
        calc.coordinate_transform()
        
        # Получаем сводку
        summary = calc.get_results_summary()
        
        return {
            "success": True,
            "robot_type": summary['robot_type'],
            "type_of_control": summary['type_of_control'],
            "spline": summary['spline'],
            "trajectory_length": summary['trajectory_length'],
            "quality_link_1": summary['quality']['link_1'],
            "quality_link_2": summary['quality']['link_2'],
        }
    except Exception as e:
        import traceback
        print(f"Error calculating trajectory: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/robot/plot/{plot_type}", response_model=PlotResponse)
def get_plot(plot_type: PlotType, session_id: str = "default"):
    """Получить график в виде base64 изображения"""
    try:
        calc = get_calculator(session_id)
        
        # Если траектория ещё не рассчитана
        if not calc.output_time_array:
            calc.calculate_trajectory()
            calc.coordinate_transform()
        
        image_base64 = calc.generate_plot(plot_type.value)
        
        if not image_base64:
            raise HTTPException(status_code=400, detail="Не удалось создать график")
        
        return {
            "success": True,
            "plot_type": plot_type.value,
            "image_base64": image_base64,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/robot/workspace", response_model=WorkspaceResponse)
def get_workspace(session_id: str = "default"):
    """Получить изображение рабочей области"""
    try:
        calc = get_calculator(session_id)
        workspace_calc = WorkspaceCalculator(calc.state)
        
        image_base64 = workspace_calc.generate_workspace_plot()
        
        return {
            "success": True,
            "robot_type": calc.state.robot_type,
            "image_base64": image_base64,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/robot/spline-cyclegram")
def get_spline_cyclegram(session_id: str = "default"):
    """Получить данные циклограммы сплайна"""
    try:
        calc = get_calculator(session_id)
        
        # Получаем данные сплайна напрямую из calculator (там они хранятся после расчёта)
        t_spline = getattr(calc, 't_spline', [])
        q1_spline = getattr(calc, 'q_1_spline', [])
        q2_spline = getattr(calc, 'q_2_spline', [])
        
        # Преобразуем в списки Python (если это numpy arrays)
        t_list = list(t_spline) if hasattr(t_spline, '__iter__') else []
        q1_list = list(q1_spline) if hasattr(q1_spline, '__iter__') else []
        q2_list = list(q2_spline) if hasattr(q2_spline, '__iter__') else []
        
        return {
            "success": True,
            "data": {
                "t": t_list,
                "q1": q1_list,
                "q2": q2_list,
            },
            "length": max(len(t_list), len(q1_list), len(q2_list)),
            "spline_enabled": calc.state.spline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/robot/data/all", response_model=AllDataResponse)
def get_all_data(session_id: str = "default"):
    """Получить все данные расчёта для построения графиков на фронтенде"""
    try:
        calc = get_calculator(session_id)
        
        # Если траектория ещё не рассчитана
        if not calc.output_time_array:
            calc.calculate_trajectory()
            calc.coordinate_transform()
        
        s = calc.state
        
        # Подготавливаем данные (ограничиваем размер для передачи)
        max_points = 10000
        step = max(1, len(calc.output_time_array) // max_points)
        
        time = calc.output_time_array[::step]
        
        return {
            "success": True,
            "trajectory": {
                "time": time,
                "q1": calc.trajectory_q_1[::step],
                "q2": calc.trajectory_q_2[::step],
                "real_x": calc.real_trajectory_x[::step] if calc.real_trajectory_x else [],
                "real_y": calc.real_trajectory_y[::step] if calc.real_trajectory_y else [],
                "cyclogram_x": calc.cyclogram_real_x,
                "cyclogram_y": calc.cyclogram_real_y,
                "cyclogram_t": s.t,
                "cyclogram_q1": s.q1,
                "cyclogram_q2": s.q2,
            },
            "electrical": {
                "time": time,
                "U_1": calc.U_array_1[::step],
                "U_2": calc.U_array_2[::step],
                "Ustar_1": calc.Ustar_array_1[::step],
                "Ustar_2": calc.Ustar_array_2[::step],
                "I_1": calc.I_array_1[::step],
                "I_2": calc.I_array_2[::step],
            },
            "mechanical": {
                "time": time,
                "M_ed_1": calc.M_ed_array_1[::step],
                "M_ed_2": calc.M_ed_array_2[::step],
                "M_load_1": calc.M1_array[::step],
                "M_load_2": calc.M2_array[::step],
                "M_corrected_1": calc.M_ed_corrected_array_1[::step],
                "M_corrected_2": calc.M_ed_corrected_array_2[::step],
                "speed_1": calc.speed_array_1[::step],
                "speed_2": calc.speed_array_2[::step],
                "acceleration_1": calc.acceleration_array_1[::step],
                "acceleration_2": calc.acceleration_array_2[::step],
            },
            "quality_link_1": {
                "errors": calc.error_1,
                "avg_error": calc.avg_error_1,
                "median_error": calc.median_error_1,
                "regulation_times": calc.reg_time_1,
                "avg_reg_time": calc.avg_reg_time_1,
                "median_reg_time": calc.median_reg_time_1,
            },
            "quality_link_2": {
                "errors": calc.error_2,
                "avg_error": calc.avg_error_2,
                "median_error": calc.median_error_2,
                "regulation_times": calc.reg_time_2,
                "avg_reg_time": calc.avg_reg_time_2,
                "median_reg_time": calc.median_reg_time_2,
            },
        }
    except Exception as e:
        import traceback
        print(f"Error getting all data: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/robot/session/{session_id}")
def delete_session(session_id: str):
    """Удалить сессию расчёта"""
    if session_id in robot_calculators:
        del robot_calculators[session_id]
        return {"success": True, "message": "Сессия удалена"}
    return {"success": False, "message": "Сессия не найдена"}


# =====================================================
# API для загрузки и сохранения файлов конфигурации
# =====================================================

from fastapi import UploadFile, File
from fastapi.responses import Response
from typing import List
import io

# Маппинг типов роботов
ROBOT_TYPE_MAP = {
    'cartesian': 'Декартовый',
    'scara': 'Скара',
    'cylindrical': 'Цилиндрический',
    'coler': 'Колер',
    'Декартовый': 'cartesian',
    'Скара': 'scara', 
    'Цилиндрический': 'cylindrical',
    'Колер': 'coler',
}


def parse_config_file(content: str) -> dict:
    """Парсинг файла конфигурации"""
    lines = content.strip().split('\n')
    
    def safe_float(s):
        try:
            return float(s.strip())
        except:
            return 0.0
    
    def safe_float_list(s):
        try:
            return [float(x.strip()) for x in s.strip().split(',')]
        except:
            return [0.0, 0.0]
    
    config = {}
    
    try:
        # Строка 0: Тип робота
        robot_type_raw = lines[0].strip()
        config['robot_type'] = ROBOT_TYPE_MAP.get(robot_type_raw, robot_type_raw)
        
        # Строки 1-4: Параметры декартового робота
        config['massd_1'] = safe_float(lines[1])
        config['massd_2'] = safe_float(lines[2])
        config['massd_3'] = safe_float(lines[3])
        config['momentd_1'] = safe_float(lines[4])
        
        # Строки 5-12: Ограничения декартового робота
        config['x_min'] = safe_float(lines[5])
        config['y_min'] = safe_float(lines[6])
        config['q_min'] = safe_float(lines[7])
        config['z_min'] = safe_float(lines[8])
        config['x_max'] = safe_float(lines[9])
        config['y_max'] = safe_float(lines[10])
        config['q_max'] = safe_float(lines[11])
        config['z_max'] = safe_float(lines[12])
        
        # Строки 13-20: Параметры SCARA
        config['moment_1'] = safe_float(lines[13])
        config['moment_2'] = safe_float(lines[14])
        config['moment_3'] = safe_float(lines[15])
        config['length_1'] = safe_float(lines[16])
        config['length_2'] = safe_float(lines[17])
        config['distance'] = safe_float(lines[18])
        config['masss_2'] = safe_float(lines[19])
        config['masss_3'] = safe_float(lines[20])
        
        # Строки 21-28: Ограничения SCARA
        config['q1s_min'] = safe_float(lines[21])
        config['q1s_max'] = safe_float(lines[22])
        config['q2s_min'] = safe_float(lines[23])
        config['q2s_max'] = safe_float(lines[24])
        config['q3s_min'] = safe_float(lines[25])
        config['q3s_max'] = safe_float(lines[26])
        config['zs_min'] = safe_float(lines[27])
        config['zs_max'] = safe_float(lines[28])
        
        # Строки 29-36: Параметры цилиндрического робота
        config['momentc_1'] = safe_float(lines[29])
        config['momentc_2'] = safe_float(lines[30])
        config['momentc_3'] = safe_float(lines[31])
        config['lengthc_1'] = safe_float(lines[32])
        config['lengthc_2'] = safe_float(lines[33])
        config['distancec'] = safe_float(lines[34])
        config['massc_2'] = safe_float(lines[35])
        config['massc_3'] = safe_float(lines[36])
        
        # Строки 37-44: Ограничения цилиндрического робота
        config['q1c_min'] = safe_float(lines[37])
        config['q1c_max'] = safe_float(lines[38])
        config['a2c_min'] = safe_float(lines[39])
        config['a2c_max'] = safe_float(lines[40])
        config['q3c_min'] = safe_float(lines[41])
        config['q3c_max'] = safe_float(lines[42])
        config['zc_min'] = safe_float(lines[43])
        config['zc_max'] = safe_float(lines[44])
        
        # Строки 45-52: Параметры робота Колер
        config['momentcol_1'] = safe_float(lines[45])
        config['momentcol_2'] = safe_float(lines[46])
        config['momentcol_3'] = safe_float(lines[47])
        config['lengthcol_1'] = safe_float(lines[48])
        config['lengthcol_2'] = safe_float(lines[49])
        config['distancecol'] = safe_float(lines[50])
        config['masscol_2'] = safe_float(lines[51])
        config['masscol_3'] = safe_float(lines[52])
        
        # Строки 53-60: Ограничения робота Колер
        config['q1col_min'] = safe_float(lines[53])
        config['q1col_max'] = safe_float(lines[54])
        config['a2col_min'] = safe_float(lines[55])
        config['a2col_max'] = safe_float(lines[56])
        config['q3col_min'] = safe_float(lines[57])
        config['q3col_max'] = safe_float(lines[58])
        config['zcol_min'] = safe_float(lines[59])
        config['zcol_max'] = safe_float(lines[60])
        
        # Строки 61-67: Параметры двигателей
        config['J'] = safe_float_list(lines[61])
        config['T_e'] = safe_float_list(lines[62])
        config['Umax'] = safe_float_list(lines[63])
        config['Fi'] = safe_float_list(lines[64])
        config['Ce'] = safe_float_list(lines[65])
        config['Ra'] = safe_float_list(lines[66])
        config['Cm'] = safe_float_list(lines[67])
        
        # Строки 68-70: Параметры ПИД
        config['Kp'] = safe_float_list(lines[68])
        config['Ki'] = safe_float_list(lines[69])
        config['Kd'] = safe_float_list(lines[70])
        
        # Строки 71-75: Циклограмма
        config['t'] = safe_float_list(lines[71])
        config['q1'] = safe_float_list(lines[72])
        config['q2'] = safe_float_list(lines[73])
        config['q3'] = safe_float_list(lines[74])
        config['q4'] = safe_float_list(lines[75])
        
        # Строка 76: Тип траектории
        if len(lines) > 76:
            config['trajectory_type'] = lines[76].strip()
        
        # Строка 77: Параметры линии
        if len(lines) > 77:
            config['line_params'] = safe_float_list(lines[77])
        
        # Строка 78: Параметры окружности
        if len(lines) > 78:
            config['circle_params'] = safe_float_list(lines[78])
            
    except Exception as e:
        print(f"Error parsing config file: {e}")
        raise ValueError(f"Ошибка парсинга файла: {e}")
    
    return config


def generate_config_file(state: dict) -> str:
    """Генерация файла конфигурации из состояния"""
    lines = []
    
    def get(key, default=0):
        return state.get(key, default) if state.get(key) is not None else default
    
    def get_list(key, default=None):
        val = state.get(key, default or [0, 0])
        return val if val else default or [0, 0]
    
    # Определяем тип робота
    robot_type = state.get('robotType', 'cartesian')
    robot_type_ru = ROBOT_TYPE_MAP.get(robot_type, robot_type)
    lines.append(robot_type_ru)
    
    # Параметры декартового робота
    cart = state.get('cartesianParams', {})
    lines.append(str(get('massd_1', cart.get('mass1', 0))))
    lines.append(str(get('massd_2', cart.get('mass2', 0))))
    lines.append(str(get('massd_3', cart.get('mass3', 0))))
    lines.append(str(get('momentd_1', cart.get('moment', 0))))
    
    # Ограничения декартового робота
    cart_lim = state.get('cartesianLimits', {})
    lines.append(str(get('x_min', cart_lim.get('Xmin', 0))))
    lines.append(str(get('y_min', cart_lim.get('Ymin', 0))))
    lines.append(str(get('q_min', cart_lim.get('Qmin', 0))))
    lines.append(str(get('z_min', cart_lim.get('Zmin', 0))))
    lines.append(str(get('x_max', cart_lim.get('Xmax', 0))))
    lines.append(str(get('y_max', cart_lim.get('Ymax', 0))))
    lines.append(str(get('q_max', cart_lim.get('Qmax', 0))))
    lines.append(str(get('z_max', cart_lim.get('Zmax', 0))))
    
    # Параметры SCARA
    scara = state.get('scaraParams', {})
    lines.append(str(get('moment_1', scara.get('moment1', 0))))
    lines.append(str(get('moment_2', scara.get('moment2', 0))))
    lines.append(str(get('moment_3', scara.get('moment3', 0))))
    lines.append(str(get('length_1', scara.get('length1', 0))))
    lines.append(str(get('length_2', scara.get('length2', 0))))
    lines.append(str(get('distance', scara.get('distance', 0))))
    lines.append(str(get('masss_2', scara.get('mass2', 0))))
    lines.append(str(get('masss_3', scara.get('mass3', 0))))
    
    # Ограничения SCARA
    scara_lim = state.get('scaraLimits', {})
    lines.append(str(get('q1s_min', scara_lim.get('q1Min', 0))))
    lines.append(str(get('q1s_max', scara_lim.get('q1Max', 0))))
    lines.append(str(get('q2s_min', scara_lim.get('q2Min', 0))))
    lines.append(str(get('q2s_max', scara_lim.get('q2Max', 0))))
    lines.append(str(get('q3s_min', scara_lim.get('q3Min', 0))))
    lines.append(str(get('q3s_max', scara_lim.get('q3Max', 0))))
    lines.append(str(get('zs_min', scara_lim.get('zMin', 0))))
    lines.append(str(get('zs_max', scara_lim.get('zMax', 0))))
    
    # Параметры цилиндрического робота
    cyl = state.get('cylindricalParams', {})
    lines.append(str(get('momentc_1', cyl.get('moment1', 0))))
    lines.append(str(get('momentc_2', cyl.get('moment2', 0))))
    lines.append(str(get('momentc_3', cyl.get('moment3', 0))))
    lines.append(str(get('lengthc_1', cyl.get('length1', 0))))
    lines.append(str(get('lengthc_2', cyl.get('length2', 0))))
    lines.append(str(get('distancec', cyl.get('distance', 0))))
    lines.append(str(get('massc_2', cyl.get('mass2', 0))))
    lines.append(str(get('massc_3', cyl.get('mass3', 0))))
    
    # Ограничения цилиндрического робота
    cyl_lim = state.get('cylindricalLimits', {})
    lines.append(str(get('q1c_min', cyl_lim.get('q1Min', 0))))
    lines.append(str(get('q1c_max', cyl_lim.get('q1Max', 0))))
    lines.append(str(get('a2c_min', cyl_lim.get('a2Min', 0))))
    lines.append(str(get('a2c_max', cyl_lim.get('a2Max', 0))))
    lines.append(str(get('q3c_min', cyl_lim.get('q3Min', 0))))
    lines.append(str(get('q3c_max', cyl_lim.get('q3Max', 0))))
    lines.append(str(get('zc_min', cyl_lim.get('zMin', 0))))
    lines.append(str(get('zc_max', cyl_lim.get('zMax', 0))))
    
    # Параметры робота Колер
    col = state.get('colerParams', {})
    lines.append(str(get('momentcol_1', col.get('moment1', 0))))
    lines.append(str(get('momentcol_2', col.get('moment2', 0))))
    lines.append(str(get('momentcol_3', col.get('moment3', 0))))
    lines.append(str(get('lengthcol_1', col.get('length1', 0))))
    lines.append(str(get('lengthcol_2', col.get('length2', 0))))
    lines.append(str(get('distancecol', col.get('distance', 0))))
    lines.append(str(get('masscol_2', col.get('mass2', 0))))
    lines.append(str(get('masscol_3', col.get('mass3', 0))))
    
    # Ограничения робота Колер
    col_lim = state.get('colerLimits', {})
    lines.append(str(get('q1col_min', col_lim.get('q1Min', 0))))
    lines.append(str(get('q1col_max', col_lim.get('q1Max', 0))))
    lines.append(str(get('a2col_min', col_lim.get('a2Min', 0))))
    lines.append(str(get('a2col_max', col_lim.get('a2Max', 0))))
    lines.append(str(get('q3col_min', col_lim.get('q3Min', 0))))
    lines.append(str(get('q3col_max', col_lim.get('q3Max', 0))))
    lines.append(str(get('zcol_min', col_lim.get('zMin', 0))))
    lines.append(str(get('zcol_max', col_lim.get('zMax', 0))))
    
    # Параметры двигателей
    motor = state.get('motorParams', {})
    lines.append(','.join(map(str, get_list('J', motor.get('J', [0, 0])))))
    lines.append(','.join(map(str, get_list('T_e', motor.get('Te', [0, 0])))))
    lines.append(','.join(map(str, get_list('Umax', motor.get('Umax', [0, 0])))))
    lines.append(','.join(map(str, get_list('Fi', motor.get('Fi', [0, 0])))))
    lines.append(','.join(map(str, get_list('Ce', motor.get('Ce', [0, 0])))))
    lines.append(','.join(map(str, get_list('Ra', motor.get('Ra', [0, 0])))))
    lines.append(','.join(map(str, get_list('Cm', motor.get('Cm', [0, 0])))))
    
    # Параметры ПИД
    reg = state.get('regulatorParams', {})
    lines.append(','.join(map(str, get_list('Kp', reg.get('Kp', [0, 0, 0, 0])))))
    lines.append(','.join(map(str, get_list('Ki', reg.get('Ki', [0, 0, 0, 0])))))
    lines.append(','.join(map(str, get_list('Kd', reg.get('Kd', [0, 0, 0, 0])))))
    
    # Циклограмма
    cycl = state.get('cyclegram', {})
    lines.append(','.join(map(str, get_list('t', cycl.get('t', [0]*9)))))
    lines.append(','.join(map(str, get_list('q1', cycl.get('q1', [0]*9)))))
    lines.append(','.join(map(str, get_list('q2', cycl.get('q2', [0]*9)))))
    lines.append(','.join(map(str, get_list('q3', cycl.get('q3', [0]*9)))))
    lines.append(','.join(map(str, get_list('q4', cycl.get('q4', [0]*9)))))
    
    # Тип траектории
    traj = state.get('trajectory', {})
    lines.append(traj.get('type', 'line'))
    
    # Параметры линии
    line = traj.get('line', {})
    line_params = [
        line.get('x1', 0) or 0,
        line.get('x2', 0) or 0,
        line.get('y1', 0) or 0,
        line.get('y2', 0) or 0,
        line.get('speed', 0) or 0,
    ]
    lines.append(','.join(map(str, line_params)))
    
    # Параметры окружности
    circle = traj.get('circle', {})
    circle_params = [
        circle.get('x', 0) or 0,
        circle.get('y', 0) or 0,
        circle.get('radius', 0) or 0,
        circle.get('speed', 0) or 0,
    ]
    lines.append(','.join(map(str, circle_params)))
    
    return '\n'.join(lines)


def config_to_frontend_state(config: dict) -> dict:
    """Преобразование конфигурации в формат состояния фронтенда"""
    robot_type = config.get('robot_type', 'cartesian')
    if robot_type in ['Декартовый', 'Скара', 'Цилиндрический', 'Колер']:
        robot_type = ROBOT_TYPE_MAP.get(robot_type, 'cartesian')
    
    state = {
        'robotType': robot_type,
        'cartesianParams': {
            'mass1': config.get('massd_1', 0),
            'mass2': config.get('massd_2', 0),
            'mass3': config.get('massd_3', 0),
            'moment': config.get('momentd_1', 0),
        },
        'cartesianLimits': {
            'Xmin': config.get('x_min', 0),
            'Xmax': config.get('x_max', 0),
            'Ymin': config.get('y_min', 0),
            'Ymax': config.get('y_max', 0),
            'Zmin': config.get('z_min', 0),
            'Zmax': config.get('z_max', 0),
            'Qmin': config.get('q_min', 0),
            'Qmax': config.get('q_max', 0),
        },
        'scaraParams': {
            'moment1': config.get('moment_1', 0),
            'moment2': config.get('moment_2', 0),
            'moment3': config.get('moment_3', 0),
            'length1': config.get('length_1', 0),
            'length2': config.get('length_2', 0),
            'distance': config.get('distance', 0),
            'mass2': config.get('masss_2', 0),
            'mass3': config.get('masss_3', 0),
        },
        'scaraLimits': {
            'q1Min': config.get('q1s_min', 0),
            'q1Max': config.get('q1s_max', 0),
            'q2Min': config.get('q2s_min', 0),
            'q2Max': config.get('q2s_max', 0),
            'q3Min': config.get('q3s_min', 0),
            'q3Max': config.get('q3s_max', 0),
            'zMin': config.get('zs_min', 0),
            'zMax': config.get('zs_max', 0),
        },
        'cylindricalParams': {
            'moment1': config.get('momentc_1', 0),
            'moment2': config.get('momentc_2', 0),
            'moment3': config.get('momentc_3', 0),
            'length1': config.get('lengthc_1', 0),
            'length2': config.get('lengthc_2', 0),
            'distance': config.get('distancec', 0),
            'mass2': config.get('massc_2', 0),
            'mass3': config.get('massc_3', 0),
        },
        'cylindricalLimits': {
            'q1Min': config.get('q1c_min', 0),
            'q1Max': config.get('q1c_max', 0),
            'a2Min': config.get('a2c_min', 0),
            'a2Max': config.get('a2c_max', 0),
            'q3Min': config.get('q3c_min', 0),
            'q3Max': config.get('q3c_max', 0),
            'zMin': config.get('zc_min', 0),
            'zMax': config.get('zc_max', 0),
        },
        'colerParams': {
            'moment1': config.get('momentcol_1', 0),
            'moment2': config.get('momentcol_2', 0),
            'moment3': config.get('momentcol_3', 0),
            'length1': config.get('lengthcol_1', 0),
            'length2': config.get('lengthcol_2', 0),
            'distance': config.get('distancecol', 0),
            'mass2': config.get('masscol_2', 0),
            'mass3': config.get('masscol_3', 0),
        },
        'colerLimits': {
            'q1Min': config.get('q1col_min', 0),
            'q1Max': config.get('q1col_max', 0),
            'a2Min': config.get('a2col_min', 0),
            'a2Max': config.get('a2col_max', 0),
            'q3Min': config.get('q3col_min', 0),
            'q3Max': config.get('q3col_max', 0),
            'zMin': config.get('zcol_min', 0),
            'zMax': config.get('zcol_max', 0),
        },
        'motorParams': {
            'J': config.get('J', [0, 0]),
            'Te': config.get('T_e', [0, 0]),
            'Umax': config.get('Umax', [0, 0]),
            'Fi': config.get('Fi', [0, 0]),
            'Ce': config.get('Ce', [0, 0]),
            'Ra': config.get('Ra', [0, 0]),
            'Cm': config.get('Cm', [0, 0]),
        },
        'regulatorParams': {
            'Kp': config.get('Kp', [0, 0, 0, 0]),
            'Ki': config.get('Ki', [0, 0, 0, 0]),
            'Kd': config.get('Kd', [0, 0, 0, 0]),
        },
        'cyclegram': {
            't': config.get('t', [0]*9),
            'q1': config.get('q1', [0]*9),
            'q2': config.get('q2', [0]*9),
            'q3': config.get('q3', [0]*9),
            'q4': config.get('q4', [0]*9),
        },
        'trajectory': {
            'type': config.get('trajectory_type', 'line'),
            'line': {
                'x1': config.get('line_params', [0, 0, 0, 0, 0])[0] if config.get('line_params') else 0,
                'x2': config.get('line_params', [0, 0, 0, 0, 0])[1] if config.get('line_params') else 0,
                'y1': config.get('line_params', [0, 0, 0, 0, 0])[2] if config.get('line_params') else 0,
                'y2': config.get('line_params', [0, 0, 0, 0, 0])[3] if config.get('line_params') else 0,
                'speed': config.get('line_params', [0, 0, 0, 0, 0])[4] if len(config.get('line_params', [])) > 4 else 0,
            },
            'circle': {
                'x': config.get('circle_params', [0, 0, 0, 0])[0] if config.get('circle_params') else 0,
                'y': config.get('circle_params', [0, 0, 0, 0])[1] if config.get('circle_params') else 0,
                'radius': config.get('circle_params', [0, 0, 0, 0])[2] if config.get('circle_params') else 0,
                'speed': config.get('circle_params', [0, 0, 0, 0])[3] if len(config.get('circle_params', [])) > 3 else 0,
            },
        },
    }
    
    return state


@app.post("/api/data/upload")
async def upload_config_file(file: UploadFile = File(...)):
    """Загрузить файл конфигурации и получить состояние для фронтенда"""
    try:
        # Читаем содержимое файла
        content = await file.read()
        
        # Пробуем разные кодировки (Windows-1251 часто используется в русских файлах)
        text_content = None
        encodings = ['utf-8', 'cp1251', 'windows-1251', 'latin-1']
        
        for encoding in encodings:
            try:
                text_content = content.decode(encoding)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if text_content is None:
            raise ValueError("Не удалось определить кодировку файла")
        
        # Парсим файл
        config = parse_config_file(text_content)
        
        # Преобразуем в формат фронтенда
        state = config_to_frontend_state(config)
        
        return {
            "success": True,
            "message": "Файл успешно загружен",
            "filename": file.filename,
            "state": state,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка при загрузке файла: {str(e)}")


@app.post("/api/data/download")
async def download_config_file(state: dict):
    """Скачать файл конфигурации из текущего состояния"""
    try:
        # Генерируем содержимое файла
        file_content = generate_config_file(state)
        
        # Кодируем в cp1251 для совместимости с десктопным приложением
        file_bytes = file_content.encode('cp1251')
        
        # Возвращаем файл
        return Response(
            content=file_bytes,
            media_type="text/plain; charset=windows-1251",
            headers={
                "Content-Disposition": "attachment; filename=robot_config.txt"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при создании файла: {str(e)}")


# =====================================================
# API для сохранения конфигураций в базу данных
# =====================================================

class SaveConfigRequest(BaseModel):
    """Запрос на сохранение конфигурации"""
    name: str
    config_data: dict
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Название не может быть пустым')
        v = v.strip()
        if len(v) > 100:
            raise ValueError('Название не должно превышать 100 символов')
        return v


class UpdateConfigRequest(BaseModel):
    """Запрос на обновление конфигурации"""
    name: Optional[str] = None
    config_data: Optional[dict] = None


class SavedConfigResponse(BaseModel):
    """Ответ с данными конфигурации"""
    id: int
    name: str
    created_at: str
    updated_at: str


class SavedConfigDetailResponse(BaseModel):
    """Детальный ответ с данными конфигурации"""
    id: int
    name: str
    config_data: dict
    created_at: str
    updated_at: str


@app.get("/api/configs", response_model=list)
def get_user_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить список сохранённых конфигураций пользователя"""
    configs = db.query(SavedConfig).filter(
        SavedConfig.user_id == current_user.id
    ).order_by(SavedConfig.updated_at.desc()).all()
    
    return [
        {
            "id": c.id,
            "name": c.name,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in configs
    ]


@app.get("/api/configs/{config_id}")
def get_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить конфигурацию по ID"""
    config = db.query(SavedConfig).filter(
        SavedConfig.id == config_id,
        SavedConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конфигурация не найдена"
        )
    
    return {
        "id": config.id,
        "name": config.name,
        "config_data": json.loads(config.config_data),
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
    }


@app.post("/api/configs")
def save_config(
    data: SaveConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Сохранить новую конфигурацию"""
    try:
        config = SavedConfig(
            user_id=current_user.id,
            name=data.name.strip(),
            config_data=json.dumps(data.config_data, ensure_ascii=False)
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        
        return {
            "success": True,
            "message": "Конфигурация сохранена",
            "id": config.id,
            "name": config.name,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при сохранении: {str(e)}"
        )


@app.put("/api/configs/{config_id}")
def update_config(
    config_id: int,
    data: UpdateConfigRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновить существующую конфигурацию"""
    config = db.query(SavedConfig).filter(
        SavedConfig.id == config_id,
        SavedConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конфигурация не найдена"
        )
    
    try:
        if data.name is not None:
            config.name = data.name.strip()
        if data.config_data is not None:
            config.config_data = json.dumps(data.config_data, ensure_ascii=False)
        
        config.updated_at = datetime.utcnow()
        db.commit()
        
        return {
            "success": True,
            "message": "Конфигурация обновлена",
            "id": config.id,
            "name": config.name,
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обновлении: {str(e)}"
        )


@app.delete("/api/configs/{config_id}")
def delete_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удалить конфигурацию"""
    config = db.query(SavedConfig).filter(
        SavedConfig.id == config_id,
        SavedConfig.user_id == current_user.id
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Конфигурация не найдена"
        )
    
    try:
        db.delete(config)
        db.commit()
        
        return {
            "success": True,
            "message": "Конфигурация удалена"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при удалении: {str(e)}"
        )


# =====================================================
# API для администратора
# =====================================================

def require_admin(current_user: User = Depends(get_current_user)):
    """Проверка что пользователь - администратор"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён. Требуются права администратора."
        )
    return current_user


async def require_admin_with_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Строгая проверка админа с валидацией сессии и IP"""
    token = credentials.credentials
    client_ip = get_remote_address(request)
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Проверяем токен
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Недействительный токен")
    except JWTError:
        raise HTTPException(status_code=401, detail="Недействительный токен")
    
    # Получаем пользователя
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_admin:
        security_logger.warning(f"Admin access denied: user={username}, IP={client_ip}")
        raise HTTPException(status_code=403, detail="Доступ запрещён")
    
    # Проверяем админ-сессию (привязка к IP)
    is_valid, error_msg = admin_session_manager.validate_session(token, client_ip, user_agent)
    if not is_valid:
        security_logger.warning(f"Admin session invalid: user={username}, IP={client_ip}, reason={error_msg}")
        raise HTTPException(status_code=401, detail=error_msg)
    
    # Логируем действие
    security_logger.info(f"Admin action: user={username}, IP={client_ip}, path={request.url.path}")
    
    return user


@app.get("/api/admin/users")
def admin_get_all_users(
    request: Request,
    admin: User = Depends(require_admin_with_session),
    db: Session = Depends(get_db)
):
    """Получить список всех пользователей (только для админа)"""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "is_admin": u.is_admin,
            "created_at": u.created_at.isoformat(),
            "configs_count": len(u.saved_configs),
        }
        for u in users
    ]


@app.get("/api/admin/users/{user_id}")
def admin_get_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin_with_session),
    db: Session = Depends(get_db)
):
    """Получить информацию о пользователе (только для админа)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return {
        "id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat(),
        "configs": [
            {
                "id": c.id,
                "name": c.name,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
            }
            for c in user.saved_configs
        ]
    }


@app.get("/api/admin/configs")
def admin_get_all_configs(
    request: Request,
    admin: User = Depends(require_admin_with_session),
    db: Session = Depends(get_db)
):
    """Получить все конфигурации всех пользователей (только для админа)"""
    configs = db.query(SavedConfig).order_by(SavedConfig.updated_at.desc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "user_id": c.user_id,
            "username": c.owner.username,
            "created_at": c.created_at.isoformat(),
            "updated_at": c.updated_at.isoformat(),
        }
        for c in configs
    ]


@app.get("/api/admin/configs/{config_id}")
def admin_get_config(
    request: Request,
    config_id: int,
    admin: User = Depends(require_admin_with_session),
    db: Session = Depends(get_db)
):
    """Получить любую конфигурацию по ID (только для админа)"""
    config = db.query(SavedConfig).filter(SavedConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Конфигурация не найдена")
    
    return {
        "id": config.id,
        "name": config.name,
        "user_id": config.user_id,
        "username": config.owner.username,
        "config_data": json.loads(config.config_data),
        "created_at": config.created_at.isoformat(),
        "updated_at": config.updated_at.isoformat(),
    }


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin_with_session),
    db: Session = Depends(get_db)
):
    """Удалить пользователя (только для админа)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    
    if user.is_admin:
        raise HTTPException(status_code=400, detail="Нельзя удалить другого администратора")
    
    try:
        db.delete(user)
        db.commit()
        return {"success": True, "message": f"Пользователь {user.username} удалён"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/admin/configs/{config_id}")
def admin_delete_config(
    request: Request,
    config_id: int,
    admin: User = Depends(require_admin_with_session),
    db: Session = Depends(get_db)
):
    """Удалить любую конфигурацию (только для админа)"""
    config = db.query(SavedConfig).filter(SavedConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Конфигурация не найдена")
    
    try:
        username = config.owner.username
        config_name = config.name
        db.delete(config)
        db.commit()
        return {"success": True, "message": f"Конфигурация '{config_name}' пользователя {username} удалена"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/admin/users/{user_id}/toggle-admin")
def admin_toggle_admin(
    request: Request,
    user_id: int,
    admin: User = Depends(require_admin_with_session),
    db: Session = Depends(get_db)
):
    """Переключить права администратора (только для админа)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Нельзя изменить свои права")
    
    user.is_admin = not user.is_admin
    db.commit()
    
    return {
        "success": True,
        "message": f"Пользователь {user.username} {'получил' if user.is_admin else 'лишён'} прав администратора",
        "is_admin": user.is_admin
    }


@app.get("/api/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
        "created_at": current_user.created_at.isoformat(),
    }


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@app.post("/api/change-password")
def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Смена пароля пользователя"""
    client_ip = get_remote_address(request)
    
    # Проверяем текущий пароль
    if not verify_password(data.current_password, current_user.hashed_password):
        security_logger.warning(f"Password change failed (wrong current): user={current_user.username}, IP={client_ip}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный текущий пароль"
        )
    
    # Валидация нового пароля
    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль должен содержать минимум 6 символов"
        )
    
    if data.current_password == data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Новый пароль должен отличаться от текущего"
        )
    
    # Хэшируем и сохраняем новый пароль
    new_hashed = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt())
    current_user.hashed_password = new_hashed.decode('utf-8')
    db.commit()
    
    security_logger.info(f"Password changed: user={current_user.username}, IP={client_ip}")
    
    return {"success": True, "message": "Пароль успешно изменён"}
