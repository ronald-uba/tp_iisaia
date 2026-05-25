"""
Modelos SQLAlchemy del dominio BookShelf.

Dos entidades con relación uno-a-muchos:
    Book 1 --- N Review

Borrar un Book borra sus Reviews en cascada (regla del contrato en CLAUDE.md).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    """Default tipado para columnas datetime — UTC aware."""
    return datetime.now(timezone.utc)


class Book(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    # published_year es opcional según el contrato.
    published_year: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=_utcnow,
        server_default=func.current_timestamp(),
    )

    # Relación uno-a-muchos con cascada de borrado.
    # cascade="all, delete-orphan" cubre el ORM; passive_deletes con
    # ondelete="CASCADE" en la FK refuerza a nivel de schema.
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    book_id: Mapped[int] = mapped_column(
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_name: Mapped[str] = mapped_column(String(120), nullable=False)
    # rating queda restringido a 1-5 por el schema Pydantic; en la BD
    # se guarda como Integer simple para mantener el modelo livianito.
    rating: Mapped[int] = mapped_column(nullable=False)
    comment: Mapped[str] = mapped_column(String(2000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=_utcnow,
        server_default=func.current_timestamp(),
    )

    book: Mapped[Book] = relationship(back_populates="reviews")
