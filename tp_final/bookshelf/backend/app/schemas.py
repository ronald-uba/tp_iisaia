"""
Schemas Pydantic v2 para validar input y serializar output.

Convención (CLAUDE.md):
    - <Entidad>Base    -> campos comunes, no se usa directamente.
    - <Entidad>Create  -> payload del POST (sin id ni created_at).
    - <Entidad>Update  -> payload del PUT, todos los campos opcionales.
    - <Entidad>Read    -> respuesta de la API, incluye id y created_at.

Nunca devolver un modelo SQLAlchemy directamente: siempre mapear con
`from_attributes=True`.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Book
# ---------------------------------------------------------------------------

class BookBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    author: str = Field(min_length=1, max_length=255)
    published_year: int | None = Field(default=None, ge=0, le=2100)


class BookCreate(BookBase):
    """Payload para POST /api/books."""


class BookUpdate(BaseModel):
    """Payload para PUT /api/books/{id}. Todos los campos opcionales."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=255)
    published_year: int | None = Field(default=None, ge=0, le=2100)


class BookRead(BookBase):
    """Respuesta de la API para un libro."""

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

class ReviewBase(BaseModel):
    reviewer_name: str = Field(min_length=1, max_length=120)
    rating: int = Field(ge=1, le=5)
    comment: str = Field(min_length=1, max_length=2000)


class ReviewCreate(ReviewBase):
    """
    Payload para POST /api/books/{id}/reviews.

    book_id NO va en el body — se toma de la URL en el router.
    """


class ReviewUpdate(BaseModel):
    """Payload para futuras ediciones de reseña. Todos los campos opcionales."""

    reviewer_name: str | None = Field(default=None, min_length=1, max_length=120)
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, min_length=1, max_length=2000)


class ReviewRead(ReviewBase):
    """Respuesta de la API para una reseña."""

    id: int
    book_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
