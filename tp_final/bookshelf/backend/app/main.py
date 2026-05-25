"""
Entry point de la app FastAPI.

Orden de montaje (importa: estático va último):
    1. Lifespan que crea las tablas en el arranque.
    2. Routers de /api.
    3. StaticFiles en /, para no interceptar rutas de la API.

Cómo levantar:
    cd backend
    uvicorn app.main:app --reload
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import create_all
from app.routers import books, reviews


@asynccontextmanager
async def lifespan(_: FastAPI):
    # create_all() es idempotente: no recrea tablas existentes.
    create_all()
    yield


app = FastAPI(
    title="BookShelf API",
    version="1.0.0",
    description="Sistema de gestión de libros y reseñas.",
    lifespan=lifespan,
)

# Routers de la API: registrar ANTES del mount de estáticos.
app.include_router(books.router)
app.include_router(reviews.router)

# Sirve frontend/ como sitio estático. directory es relativo al cwd desde el
# que se levanta uvicorn (que por convención es backend/, según CLAUDE.md).
# html=True devuelve index.html para "/".
app.mount(
    "/",
    StaticFiles(directory="../frontend", html=True),
    name="static",
)
