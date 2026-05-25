"""
Configuración de SQLAlchemy: engine, sesión y dependencia para FastAPI.

El archivo de base de datos vive en backend/bookshelf.db (relativo al cwd desde
donde se levanta uvicorn). Si se modifica algún modelo hay que borrar el archivo
y reiniciar la app — no hay sistema de migraciones por decisión arquitectónica.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# URL local: archivo SQLite junto al cwd del proceso uvicorn (backend/).
DATABASE_URL = "sqlite:///./bookshelf.db"

# check_same_thread=False es necesario porque FastAPI maneja requests en
# múltiples threads y SQLite por defecto rechaza conexiones cruzadas.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Fábrica de sesiones. autoflush=False evita sorpresas en lecturas.
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Clase base para todos los modelos declarativos."""


def get_db() -> Generator[Session, None, None]:
    """
    Dependencia de FastAPI: abre una sesión por request y la cierra al final.
    Usar con `Depends(get_db)` en los routers.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all() -> None:
    """Crea todas las tablas declaradas en los modelos. Idempotente."""
    # Import perezoso para evitar ciclos: los modelos importan Base desde acá.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
