from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import bcrypt

# База данных SQLite с поддержкой Unicode
DATABASE_URL = "sqlite:///./users.db?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},
    echo=False  # Установите True для отладки SQL запросов
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(30), unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)  # Флаг администратора
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связь с сохранёнными конфигурациями
    saved_configs = relationship("SavedConfig", back_populates="owner", cascade="all, delete-orphan")


class SavedConfig(Base):
    """Сохранённые конфигурации роботов пользователей"""
    __tablename__ = "saved_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)  # Название конфигурации
    config_data = Column(Text, nullable=False)  # JSON данные конфигурации
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связь с пользователем
    owner = relationship("User", back_populates="saved_configs")


# Создаем таблицы
def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Миграция: добавляем столбец is_admin если его нет
    import sqlite3
    try:
        conn = sqlite3.connect('./users.db')
        cursor = conn.cursor()
        # Проверяем есть ли столбец is_admin
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'is_admin' not in columns:
            print("Миграция: добавление столбца is_admin...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            conn.commit()
            print("Миграция завершена успешно")
        conn.close()
    except Exception as e:
        print(f"Ошибка миграции: {e}")


# Получить сессию БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Создать администратора при первом запуске
def create_admin_user(username: str = "admin", password: str = "admin123"):
    """Создаёт пользователя-администратора если его нет"""
    db = SessionLocal()
    try:
        # Проверяем есть ли уже админ
        admin = db.query(User).filter(User.username == username).first()
        if admin:
            # Если пользователь существует но не админ - делаем админом
            try:
                current_is_admin = admin.is_admin
            except:
                current_is_admin = False
            
            if not current_is_admin:
                admin.is_admin = True
                db.commit()
                print(f"Пользователь '{username}' получил права администратора")
            else:
                print(f"Администратор '{username}' уже существует")
            return admin
        
        # Создаём нового админа
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        admin = User(
            username=username,
            hashed_password=hashed.decode('utf-8'),
            is_admin=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"Создан администратор: {username} (пароль: {password})")
        print("ВАЖНО: Смените пароль администратора после первого входа!")
        return admin
    except Exception as e:
        db.rollback()
        print(f"Ошибка создания администратора: {e}")
        return None
    finally:
        db.close()

