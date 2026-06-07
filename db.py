import os
import base64
import hashlib
import hmac
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, select
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    display_name = Column(String(120), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    derived_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return f"{base64.b64encode(salt).decode('utf-8')}:{base64.b64encode(derived_key).decode('utf-8')}"


def _verify_password(password, encoded_value):
    try:
        encoded_salt, encoded_hash = encoded_value.split(":", 1)
        salt = base64.b64decode(encoded_salt.encode("utf-8"))
        expected_hash = base64.b64decode(encoded_hash.encode("utf-8"))
    except Exception:
        return False

    candidate_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
    return hmac.compare_digest(candidate_hash, expected_hash)

def init_db():
    Base.metadata.create_all(bind=engine)


def register_user(username, password, display_name=None):
    cleaned_username = (username or "").strip().lower()
    cleaned_display_name = (display_name or "").strip() or cleaned_username

    if len(cleaned_username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters long."

    with SessionLocal() as db:
        existing_user = db.execute(select(User).where(User.username == cleaned_username)).scalar_one_or_none()
        if existing_user:
            return False, "Username already exists."

        user = User(
            username=cleaned_username,
            password_hash=_hash_password(password),
            display_name=cleaned_display_name,
        )
        db.add(user)
        db.commit()

    return True, "Registration successful."


def authenticate_user(username, password):
    cleaned_username = (username or "").strip().lower()
    if not cleaned_username or not password:
        return False, None

    with SessionLocal() as db:
        user = db.execute(select(User).where(User.username == cleaned_username)).scalar_one_or_none()
        if not user:
            return False, None

        if not _verify_password(password, user.password_hash):
            return False, None

        return True, {"id": user.id, "username": user.username, "display_name": user.display_name}