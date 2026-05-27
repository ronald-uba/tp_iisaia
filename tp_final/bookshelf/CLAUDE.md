# BookShelf

Sistema de gestión de libros y reseñas. Trabajo práctico para la materia Inteligencia Aplicada al Desarrollo de Software.

## Stack

- **Backend**: FastAPI (Python 3.11+) con Pydantic v2
- **ORM**: SQLAlchemy 2.x
- **Base de datos**: SQLite (archivo local `bookshelf.db`)
- **Frontend**: HTML5, CSS3 y JavaScript vanilla (sin frameworks, sin build step)
- **Servidor estático**: el mismo FastAPI sirve los archivos del frontend
- **Gestor de paquetes Python**: pip + venv

Un solo proceso, un solo lenguaje del lado del servidor, cero pasos de build.

## Estructura del repositorio

```
bookshelf/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entry point FastAPI, monta /api y estáticos
│   │   ├── database.py          # Engine, SessionLocal, get_db, create_all
│   │   ├── models.py            # Modelos SQLAlchemy (Book, Review)
│   │   ├── schemas.py           # Schemas Pydantic (request/response)
│   │   ├── crud.py              # Funciones de acceso a datos
│   │   └── routers/
│   │       ├── books.py         # Endpoints de libros
│   │       └── reviews.py       # Endpoints de reseñas
│   ├── tests/
│   ├── requirements.txt
│   ├── bookshelf.db             # Generado al arrancar (no versionar)
│   └── .venv/                   # No versionar
├── frontend/
│   ├── index.html               # Página única
│   ├── styles.css
│   └── app.js                   # Lógica de UI y llamadas a la API
├── .claude/
│   ├── settings.json            # Restricciones de permisos
│   └── skills/                  # Skills propias
├── CLAUDE.md                    # Este archivo
└── README.md
```

## Modelo de dominio

Dos entidades (`Book` y `Review`) con relación uno-a-muchos. Un libro tiene muchas reseñas; borrar un libro borra sus reseñas en cascada. Los campos exactos viven en `backend/app/models.py`.

## Inicialización de la base

La base se crea automáticamente al arrancar la app con `Base.metadata.create_all(bind=engine)` en `database.py`. No hay sistema de migraciones. Si se modifica un modelo, borrar `bookshelf.db` y reiniciar la app.

## Contrato API

Base URL: `http://localhost:8000/api`. La especificación completa (endpoints, schemas, códigos de estado) está autogenerada en `/docs` (Swagger UI) y es la fuente de verdad. Los routers viven en `backend/app/routers/`.

Decisiones de diseño que no se ven en Swagger y deben respetarse:

- **Búsqueda**: `GET /api/books?q=<texto>` filtra por `title` o `author` (case-insensitive, substring). Sin `q` devuelve todos. No paginada — suficiente para el volumen del TP.
- **Borrado de libro**: hace cascada sobre sus reviews.
- **Errores**: formato estándar de FastAPI `{ "detail": "..." }`.
- **Archivos estáticos**: el frontend se sirve con un `StaticFiles` montado en `/`. Ese mount va **al final** de `main.py`, después de registrar los routers de `/api`, para no interceptar las rutas de la API.

## Convenciones de código

### Backend

- **Naming**: `snake_case` para variables, funciones, archivos y columnas de BD. `PascalCase` para clases.
- **Schemas Pydantic**: tres variantes por entidad. `BookBase` (campos comunes), `BookCreate` (input de POST), `BookRead` (output con `id` y `created_at`). Para PUT usar `BookUpdate` con todos los campos opcionales.
- **Modelos vs Schemas**: nunca devolver un modelo SQLAlchemy directamente. Siempre mapear a un schema Pydantic con `from_attributes=True`.
- **Routers**: agrupar por recurso, uno por archivo, con `prefix` y `tags` definidos.
- **CRUD**: lógica de acceso a datos en `app/crud.py`, no en los routers. Los routers solo validan, llaman al CRUD y devuelven.
- **Inyección de dependencias**: usar `Depends(get_db)` para sesiones. Nunca instanciar sesiones manualmente en routers.
- **CORS**: no es necesario porque el frontend se sirve desde el mismo origen que la API.

### Frontend

- **Un solo archivo JS**: `app.js`. Sin módulos ES, sin imports, sin bundlers.
- **Naming**: `camelCase` para variables y funciones, `kebab-case` para clases CSS e IDs.
- **Llamadas a la API**: usar `fetch`. Centralizar las llamadas en funciones con prefijo `api`, por ejemplo `apiGetBooks()`, `apiCreateBook(data)`.
- **DOM**: manipular con `document.querySelector` y `addEventListener`. No usar jQuery ni librerías externas.
- **Renderizado**: funciones `render*` que reciben datos y producen HTML como string o nodos. Una función por vista.
- **Estado**: variables a nivel de módulo. No introducir librerías de estado.
- **Estilos**: CSS plano en `styles.css`. Sin preprocesadores.

## Comandos comunes

```bash
cd backend
python -m venv .venv
source .venv/bin/activate         # Linux/Mac
# .venv\Scripts\activate          # Windows
pip install -r requirements.txt

uvicorn app.main:app --reload     # Levanta la app completa en :8000
pytest                             # Correr tests
```

Una vez levantado:
- Frontend: `http://localhost:8000/`
- API docs: `http://localhost:8000/docs`

## Reglas para el agente

Estas reglas son obligatorias. No aplicarlas equivale a salirse del plan acordado.

1. **No instalar dependencias sin avisar.** Antes de agregar una librería, justificar por qué y esperar confirmación.
2. **No modificar `requirements.txt` a mano.** Usar `pip install <pkg>` y luego `pip freeze > requirements.txt`.
3. **No introducir frameworks de frontend, bundlers, ni dependencias JS.** El frontend es vanilla por decisión arquitectónica.
4. **No borrar `bookshelf.db` sin confirmación explícita.**
5. **Respetar el contrato API.** Si una tarea sugiere cambiar un endpoint, actualizar primero esta sección de `CLAUDE.md` y los schemas Pydantic, y luego el frontend.
6. **Un cambio, un alcance.** No mezclar refactors con features nuevas en la misma tanda.
7. **Tests al tocar CRUD.** Si se modifica `app/crud.py`, agregar o actualizar el test correspondiente en `backend/tests/`.
8. **Ante ambigüedad, preguntar.** No inventar requerimientos ni asumir comportamientos no especificados.
9. **No usar `rm -rf`, `DROP TABLE`, ni operaciones destructivas sin confirmación.**
10. **Idioma**: comentarios y mensajes de commit en español. Identificadores de código en inglés.

## Flujo de trabajo típico

Para agregar una funcionalidad nueva:

1. Definir o ajustar el contrato en `CLAUDE.md` (endpoints, schemas).
2. Crear o modificar el modelo SQLAlchemy en `backend/app/models.py`.
3. Definir o actualizar schemas Pydantic en `backend/app/schemas.py`.
4. Implementar funciones CRUD en `backend/app/crud.py`.
5. Crear o actualizar el router en `backend/app/routers/` y registrarlo en `main.py`.
6. Agregar test en `backend/tests/`.
7. Agregar la función al cliente en `frontend/app.js` con prefijo `api`.
8. Implementar o actualizar la UI en `frontend/index.html` y `frontend/app.js`.
