"""
Endpoints para el recurso Book.

Solo orquestación: validar (vía Pydantic), llamar al CRUD, devolver schema.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud, schemas
from app.database import get_db

router = APIRouter(prefix="/api/books", tags=["books"])


@router.get("", response_model=list[schemas.BookRead])
def list_books(
    q: str | None = Query(
        default=None,
        description="Búsqueda case-insensitive por substring en title o author.",
        max_length=255,
    ),
    db: Session = Depends(get_db),
) -> list[schemas.BookRead]:
    return crud.list_books(db, q=q)


@router.post(
    "",
    response_model=schemas.BookRead,
    status_code=status.HTTP_201_CREATED,
)
def create_book(
    payload: schemas.BookCreate,
    db: Session = Depends(get_db),
) -> schemas.BookRead:
    return crud.create_book(db, payload)


@router.get("/{book_id}", response_model=schemas.BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> schemas.BookRead:
    book = crud.get_book(db, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado",
        )
    return book


@router.put("/{book_id}", response_model=schemas.BookRead)
def update_book(
    book_id: int,
    payload: schemas.BookUpdate,
    db: Session = Depends(get_db),
) -> schemas.BookRead:
    book = crud.update_book(db, book_id, payload)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado",
        )
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)) -> None:
    if not crud.delete_book(db, book_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado",
        )
    # 204 No Content: no devolver body.
    return None
