"""Tests para la búsqueda de libros en crud.list_books."""

from __future__ import annotations

import pytest

from app import crud, schemas


@pytest.fixture()
def sample_books(db):
    """Crea 4 libros con títulos/autores variados para los tests de búsqueda."""
    libros = [
        schemas.BookCreate(title="Rayuela", author="Julio Cortázar"),
        schemas.BookCreate(title="Ficciones", author="Jorge Luis Borges"),
        schemas.BookCreate(title="El Aleph", author="Jorge Luis Borges"),
        schemas.BookCreate(title="Pedro Páramo", author="Juan Rulfo"),
    ]
    for libro in libros:
        crud.create_book(db, libro)
    return libros


def test_list_books_sin_q_devuelve_todos(db, sample_books):
    resultados = crud.list_books(db)
    assert len(resultados) == 4


def test_list_books_q_none_devuelve_todos(db, sample_books):
    resultados = crud.list_books(db, q=None)
    assert len(resultados) == 4


def test_list_books_q_vacio_devuelve_todos(db, sample_books):
    # Una q="" debe considerarse "sin filtro".
    resultados = crud.list_books(db, q="")
    assert len(resultados) == 4


def test_list_books_busqueda_por_titulo(db, sample_books):
    resultados = crud.list_books(db, q="rayuela")
    assert [b.title for b in resultados] == ["Rayuela"]


def test_list_books_busqueda_por_autor(db, sample_books):
    resultados = crud.list_books(db, q="Borges")
    titulos = {b.title for b in resultados}
    assert titulos == {"Ficciones", "El Aleph"}


def test_list_books_es_case_insensitive(db, sample_books):
    resultados = crud.list_books(db, q="BORGES")
    assert len(resultados) == 2


def test_list_books_substring_parcial(db, sample_books):
    # "alep" debería matchear "El Aleph".
    resultados = crud.list_books(db, q="alep")
    assert [b.title for b in resultados] == ["El Aleph"]


def test_list_books_sin_resultados(db, sample_books):
    resultados = crud.list_books(db, q="zzzz-no-existe")
    assert resultados == []
