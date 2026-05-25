"""
Endpoints para el recurso Review.

Cubre dos sub-rutas del contrato:
    GET  /api/books/{book_id}/reviews
    POST /api/books/{book_id}/reviews
    DELETE /api/reviews/{review_id}

Por eso el prefix del router es "/api" y no "/api/reviews": los listados
y creaciones cuelgan del libro, pero la baja directa va por /reviews/{id}.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api", tags=["reviews"])


@router.get(
    "/books/{book_id}/reviews",
    response_model=list[schemas.ReviewRead],
)
def list_reviews(
    book_id: int,
    db: Session = Depends(get_db),
) -> list[schemas.ReviewRead]:
    reviews = crud.list_reviews_by_book(db, book_id)
    if reviews is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado",
        )
    return reviews


@router.post(
    "/books/{book_id}/reviews",
    response_model=schemas.ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    book_id: int,
    payload: schemas.ReviewCreate,
    db: Session = Depends(get_db),
) -> schemas.ReviewRead:
    review = crud.create_review(db, book_id, payload)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado",
        )
    return review


@router.delete(
    "/reviews/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_review(review_id: int, db: Session = Depends(get_db)) -> None:
    if not crud.delete_review(db, review_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reseña no encontrada",
        )
    return None
