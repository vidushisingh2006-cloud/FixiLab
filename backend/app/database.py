from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from pathlib import Path
import sqlite3
import tempfile
import uuid
import os

# Resolve backend root directory reliably
BACKEND_DIR = Path(__file__).resolve().parent.parent


def _resolve_database_path() -> Path:
    """Return a writable, lockable SQLite database path."""
    env_url = os.environ.get("DATABASE_PATH")
    if env_url:
        return Path(env_url)

    candidate = BACKEND_DIR / "fixilab.db"
    try:
        BACKEND_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(candidate))
        conn.execute("CREATE TABLE IF NOT EXISTS _healthcheck (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()
        return candidate
    except Exception:
        # Fallback to system temp directory if current mount blocks SQLite file locking
        fallback = Path(tempfile.gettempdir()) / "fixilab.db"
        return fallback


DATABASE_PATH = _resolve_database_path()
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Audit(Base):
    __tablename__ = "audits"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    status = Column(String, default="uploaded")  # uploaded, extracting, extracted, validating, completed, failed
    extraction_data = Column(Text)  # JSON serialized extraction items
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    findings = relationship("Finding", back_populates="audit", cascade="all, delete-orphan")


class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    audit_id = Column(String, ForeignKey("audits.id"), nullable=False)
    category = Column(String, nullable=False)  # calculation, documentation, consistency, alcoa
    severity = Column(String, nullable=False)  # critical, major, minor, review_required
    description = Column(Text, nullable=False)
    extracted_value = Column(String)
    expected_value = Column(String)
    page_number = Column(Integer)
    evidence = Column(Text)
    validation_rule = Column(Text)
    confidence = Column(Float)
    reviewer_comments = Column(Text)
    review_status = Column(String, default="open")  # open, accepted, resolved, needs_review
    created_at = Column(DateTime, default=datetime.utcnow)

    audit = relationship("Audit", back_populates="findings")


def _apply_lightweight_migrations():
    """Add columns introduced after a table was first created.

    SQLite's CREATE TABLE IF NOT EXISTS never alters existing tables, so databases
    created by older versions miss new model columns. Add them explicitly here.
    """
    model_columns = {
        "audits": {
            "extraction_data": "TEXT",
        },
        "findings": {
            "reviewer_comments": "TEXT",
            "review_status": "VARCHAR",
        },
    }
    with engine.begin() as conn:
        for table, columns in model_columns.items():
            existing = {row[1] for row in conn.exec_driver_sql(f"PRAGMA table_info({table})")}
            if not existing:
                continue
            for column, ddl_type in columns.items():
                if column not in existing:
                    conn.exec_driver_sql(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")


def init_db():
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
