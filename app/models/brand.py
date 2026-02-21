from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.perfume import Perfume


class Brand(Base, TimestampMixin):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    fragrantica_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    perfumes: Mapped[list["Perfume"]] = relationship(back_populates="brand", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("name", name="uq_brands_name"),
        UniqueConstraint("slug", name="uq_brands_slug"),
    )
