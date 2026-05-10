"""
Database models and initialization using SQLAlchemy ORM.

- Local development : uses SQLite  (database/database.db)
- Streamlit Cloud   : uses PostgreSQL via DATABASE_URL secret
                      (set this in Streamlit Cloud → App settings → Secrets)
"""

import os
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    DateTime, Date, Text, ForeignKey, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

# ── Resolve DATABASE_URL: st.secrets (Cloud) → env var (local) ───────────────
def _get_database_url() -> str:
    try:
        import streamlit as st
        url = st.secrets.get("DATABASE_URL", "")
        if url:
            return url
    except Exception:
        pass
    return os.getenv("DATABASE_URL", "")

DATABASE_URL = _get_database_url()

if DATABASE_URL:
    # Supabase / Heroku Postgres may give 'postgres://' — SQLAlchemy needs 'postgresql://'
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"sslmode": "require"},
    )
else:
    # Local SQLite fallback
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH  = os.path.join(BASE_DIR, "database", "database.db")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ── ORM Models ───────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    id             = Column(Integer, primary_key=True, index=True)
    username       = Column(String(50),  unique=True, nullable=False)
    email          = Column(String(120), unique=True, nullable=False)
    password_hash  = Column(String(256), nullable=False)
    monthly_budget = Column(Float, default=0.0)
    created_at     = Column(DateTime, default=datetime.utcnow)

    tasks    = relationship("Task",    back_populates="user", cascade="all, delete")
    habits   = relationship("Habit",   back_populates="user", cascade="all, delete")
    expenses = relationship("Expense", back_populates="user", cascade="all, delete")
    goals    = relationship("Goal",    back_populates="user", cascade="all, delete")


class Task(Base):
    __tablename__ = "tasks"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_name  = Column(String(200), nullable=False)
    category   = Column(String(50),  default="General")
    priority   = Column(String(20),  default="Medium")
    due_date   = Column(Date, nullable=True)
    status     = Column(String(20),  default="Pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="tasks")


class Habit(Base):
    __tablename__ = "habits"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    habit_name      = Column(String(200), nullable=False)
    streak          = Column(Integer, default=0)
    completion_date = Column(Date, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    user      = relationship("User",        back_populates="habits")
    check_ins = relationship("HabitCheckIn", back_populates="habit", cascade="all, delete")


class HabitCheckIn(Base):
    __tablename__ = "habit_checkins"
    id       = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    date     = Column(Date, default=datetime.utcnow().date)

    habit = relationship("Habit", back_populates="check_ins")


class Expense(Base):
    __tablename__ = "expenses"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount      = Column(Float, nullable=False)
    category    = Column(String(50), default="Other")
    description = Column(Text, nullable=True)
    date        = Column(Date, default=datetime.utcnow().date)
    created_at  = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="expenses")


class Goal(Base):
    __tablename__ = "goals"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_name  = Column(String(200), nullable=False)
    target     = Column(Float, default=100.0)
    progress   = Column(Float, default=0.0)
    deadline   = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")


# ── Helpers ───────────────────────────────────────────────────────────────────

def init_db():
    """Create all tables. Safe to call on every startup."""
    Base.metadata.create_all(bind=engine)
    # SQLite-only migration: add monthly_budget if missing on old DBs
    if not DATABASE_URL:
        with engine.connect() as conn:
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN monthly_budget REAL DEFAULT 0.0"))
                conn.commit()
            except Exception:
                pass


def get_session():
    return SessionLocal()


def get_user_budget(user_id: int) -> float:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        return user.monthly_budget if user else 0.0
    finally:
        session.close()


def set_user_budget(user_id: int, budget: float) -> None:
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            user.monthly_budget = budget
            session.commit()
    finally:
        session.close()
