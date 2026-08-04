from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from .config import DB_PATH, ensure_dirs


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    samples: Mapped[list[Sample]] = relationship(
        "Sample", back_populates="dataset", cascade="all, delete-orphan"
    )


class Sample(Base):
    __tablename__ = "samples"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id"))
    audio_path: Mapped[str] = mapped_column(Text)
    transcript: Mapped[str] = mapped_column(Text, default="")
    split: Mapped[str] = mapped_column(String(16), default="train")  # train | val
    duration_sec: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    dataset: Mapped[Dataset] = relationship("Dataset", back_populates="samples")


class FinetuneJob(Base):
    __tablename__ = "finetune_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(64), ForeignKey("datasets.id"))
    base_model: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="queued")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    logs: Mapped[str] = mapped_column(Text, default="")
    adapter_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    cancelled: Mapped[int] = mapped_column(Integer, default=0)

    def get_config(self) -> dict[str, Any]:
        return json.loads(self.config_json or "{}")


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(64))
    base_model: Mapped[str] = mapped_column(String(128))
    adapter_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    split: Mapped[str] = mapped_column(String(16), default="val")
    results_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


ensure_dirs()
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
