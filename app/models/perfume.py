from __future__ import annotations

import enum
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SessionStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"


class NoteType(str, enum.Enum):
    top = "top"
    middle = "middle"
    base = "base"


class Perfume(Base, TimestampMixin):
    __tablename__ = "perfumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    concentration: Mapped[str] = mapped_column(String(64), nullable=False)
    gender: Mapped[str] = mapped_column(String(32), nullable=False)
    fragrantica_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    brand: Mapped["Brand"] = relationship(back_populates="perfumes")
    notes: Mapped[list["PerfumeNote"]] = relationship(back_populates="perfume", cascade="all, delete-orphan")
    accords: Mapped[list["PerfumeAccord"]] = relationship(back_populates="perfume", cascade="all, delete-orphan")
    embeddings: Mapped[list["PerfumeEmbedding"]] = relationship(back_populates="perfume", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("brand_id", "slug", name="uq_perfumes_brand_slug"),)


class PerfumeNote(Base):
    __tablename__ = "perfume_notes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfumes.id", ondelete="CASCADE"), nullable=False)
    note_name: Mapped[str] = mapped_column(String(255), nullable=False)
    note_type: Mapped[NoteType] = mapped_column(String(16), nullable=False)

    perfume: Mapped["Perfume"] = relationship(back_populates="notes")


class PerfumeAccord(Base):
    __tablename__ = "perfume_accords"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfumes.id", ondelete="CASCADE"), nullable=False)
    accord_name: Mapped[str] = mapped_column(String(255), nullable=False)
    strength: Mapped[float] = mapped_column()

    perfume: Mapped["Perfume"] = relationship(back_populates="accords")


class PerfumeEmbedding(Base):
    __tablename__ = "perfume_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    perfume_id: Mapped[int] = mapped_column(ForeignKey("perfumes.id", ondelete="CASCADE"), nullable=False)
    embedding: Mapped[Vector] = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

    perfume: Mapped["Perfume"] = relationship(back_populates="embeddings")

    __table_args__ = (UniqueConstraint("perfume_id", name="uq_perfume_embeddings_perfume_id"),)


class CrawlStateLog(Base):
    __tablename__ = "crawl_state_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_key: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(String(16), nullable=False)
    total_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processed_pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
