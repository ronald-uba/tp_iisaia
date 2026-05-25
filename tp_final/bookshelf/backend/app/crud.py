"""
Funciones de acceso a datos.

Los routers nunca tocan la sesión directamente: validan input, llaman acá y
devuelven. Toda función recibe la `Session` como primer parámetro.

Convenciones:
    - `get_*` y `list_*` devuelven el modelo o None / lista vacía.
    - `create_*` y `update_*` devuelven el modelo persistido.
    - `delete_*` devuelve True/False según si encontró el recurso.
    - Si una operación sobre Review depende de un Book inexistente,
      la función devuelve None para que el router lo traduzca a 404.
"""

from __future__ import annotations

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app import models, schemas


# ---------------------------------------------------------------------------
# Book
# ---------------------------------------------------------------------------

def list_books(db: Session, q: str | None = None) -> list[models.Book]:
    """
    Lista libros. Si `q` no es vacío, filtra por substring case-insensitive
    sobre `title` o `author`.
    """
    query = db.query(models.Book)
    if q:
        # Normalizamos ambos lados a lower-case para no depender del collation
        # de SQLite (que con ASCII default ya es insensible, pero esto cubre
        # caracteres acentuados de forma consistente).
        pattern = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(models.Book.title).like(pattern),
                func.lower(models.Book.author).like(pattern),
            )
        )
    return query.order_by(models.Book.id).all()


def get_book(db: Session, book_id: int) -> models.Book | None:
    return db.get(models.Book, book_id)


def create_book(db: Session, data: schemas.BookCreate) -> models.Book:
    book = models.Book(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def update_book(
    db: Session, book_id: int, data: schemas.BookUpdate
) -> models.Book | None:
    book = db.get(models.Book, book_id)
    if book is None:
        return None
    # exclude_unset evita pisar campos que el cliente no envió.
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(book, key, value)
    db.commit()
    db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> bool:
    book = db.get(models.Book, book_id)
    if book is None:
        return False
    # La cascada definida en el modelo borra las reseñas asociadas.
    db.delete(book)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

def list_reviews_by_book(
    db: Session, book_id: int
) -> list[models.Review] | None:
    """Devuelve None si el libro no existe; lista (posiblemente vacía) si sí."""
    if db.get(models.Book, book_id) is None:
        return None
    return (
        db.query(models.Review)
        .filter(models.Review.book_id == book_id)
        .order_by(models.Review.id)
        .all()
    )


def create_review(
    db: Session, book_id: int, data: schemas.ReviewCreate
) -> models.Review | None:
    """Devuelve None si el libro no existe."""
    if db.get(models.Book, book_id) is None:
        return None
    review = models.Review(book_id=book_id, **data.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def delete_review(db: Session, review_id: int) -> bool:
    review = db.get(models.Review, review_id)
    if review is None:
        return False
    db.delete(review)
    db.commit()
    return True
