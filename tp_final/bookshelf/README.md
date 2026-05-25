# BookShelf — bitácora de desarrollo

Trabajo práctico final de **Inteligencia Aplicada al Desarrollo de Software**.

Este README no es un manual de uso al uso clásico: es la **bitácora de cómo se
construyó BookShelf colaborando con un agente de IA**, qué decisiones se
tomaron en cada paso y qué iteraciones hubo después de la versión inicial.
El objetivo es que cualquiera que lea esto pueda reconstruir el proceso, no
solo el resultado.

---

## 1. Metodología: arquitecto y desarrollador

El proyecto se trabajó con dos roles claramente separados:

- **Arquitecto / supervisor técnico** (el humano): define el contrato, las
  reglas, aprueba o rechaza cada fase, y mantiene el control de las decisiones
  estructurales.
- **Desarrollador** (Claude Code): ejecuta cada fase **una a la vez**, justifica
  decisiones, no avanza a la siguiente fase sin aprobación explícita, y pregunta
  ante ambigüedad en vez de inventar requerimientos.

Esta división era importante porque permite que el contexto del agente no se
sature con detalles de fases pasadas, y porque obliga al humano a leer y
validar cada entrega — evitando que el código se acumule sin control.

---

## 2. El contrato: `CLAUDE.md`

Antes de pedirle al agente que escriba una sola línea de código, se escribió
[`CLAUDE.md`](CLAUDE.md), que funciona como **constitución del proyecto**. Es
el primer archivo que el agente lee y al que vuelve siempre que tiene una duda.

### ¿Qué hay dentro de `CLAUDE.md`?

El archivo establece, en este orden:

1. **Stack tecnológico**: FastAPI + Pydantic v2, SQLAlchemy 2.x, SQLite local,
   frontend vanilla (HTML + CSS + JS sin build step). Un solo proceso, un solo
   lenguaje del lado del servidor.
2. **Estructura de carpetas exacta**: árbol de directorios que el agente debía
   crear sin desviarse. Sirve como mapa y como check contra desorden.
3. **Modelo de dominio**: `Book` y `Review` con relación uno-a-muchos y
   borrado en cascada.
4. **Contrato API**: cada endpoint con su verbo, ruta, comportamiento esperado
   y códigos de estado (200, 201, 204, 404, 422). Aquí también se fija la
   forma de los errores: `{ "detail": "..." }`.
5. **Convenciones de código**: `snake_case` para variables/funciones/columnas,
   `PascalCase` para clases, tres variantes de schemas Pydantic por entidad
   (`Base`, `Create`, `Read`, más `Update` para PUT), separación estricta
   entre routers (orquestación) y `crud.py` (acceso a datos), inyección de
   dependencias con `Depends(get_db)`. En el frontend: un solo `app.js`, sin
   imports, llamadas a la API con prefijo `api*`, render con funciones
   `render*`.
6. **Comandos comunes**: cómo levantar el venv, instalar deps, correr la app
   y los tests.
7. **Reglas obligatorias para el agente** (10 reglas). Las más usadas durante
   la conversación:
   - Regla 1: no instalar dependencias sin avisar.
   - Regla 4: no borrar `bookshelf.db` sin confirmación.
   - Regla 5: si cambia un endpoint, actualizar **primero** `CLAUDE.md`, luego
     schemas, luego frontend.
   - Regla 7: si se toca `crud.py`, agregar o actualizar tests.
   - Regla 8: ante ambigüedad, preguntar.
   - Regla 10: identificadores en inglés, comentarios y commits en español.
8. **Flujo de trabajo típico** para agregar una funcionalidad nueva, paso a
   paso desde el contrato hasta la UI.

Tener este archivo permitió que las conversaciones con el agente fueran cortas:
en vez de repetir convenciones, alcanzaba con apuntar a la regla N de
`CLAUDE.md`.

---

## 3. El primer prompt

El [primer prompt](../prompts/1st%20prompt.txt) fijó el marco de toda la
interacción. Está conservado tal cual:

> Actuá como mi desarrollador de software. Yo seré el arquitecto y supervisor
> técnico de este proyecto. Nuestro objetivo es construir el sistema BookShelf
> de manera ordenada.
>
> Toda la arquitectura, el modelo de dominio, el contrato de la API y las
> reglas de trabajo están estrictamente definidas en el archivo CLAUDE.md
> ubicado en este directorio. Debés leerlo exhaustivamente antes de escribir
> una sola línea de código.
>
> Para evitar saturar tu memoria de contexto y para que yo pueda mantener el
> control arquitectónico, trabajaremos en fases iterativas. Tenés estrictamente
> prohibido avanzar a la siguiente fase hasta que yo revise y apruebe la fase
> actual.

A continuación el prompt enumeraba las cuatro fases y terminaba con: *"Confirmá
que leíste y entendiste el archivo CLAUDE.md y estas instrucciones. Una vez
confirmes, ejecutá únicamente la Fase 1 e informame cuando esté lista para mi
evaluación."*

El agente arrancó respondiendo con un resumen del contrato y las reglas para
demostrar que había leído `CLAUDE.md` — y solo después arrancó con la Fase 1.

---

## 4. Las cuatro fases

### Fase 1 — Entorno y Claude Code

**Pedido**: estructura de carpetas, `requirements.txt`, `.claude/settings.json`
con restricciones de seguridad, y una skill propia accesible por slash command.

**Decisiones que tomó el desarrollador**:

- En `requirements.txt`: FastAPI, Uvicorn, SQLAlchemy, Pydantic, Pytest y
  HTTPX — sin pins exactos, para no atar el venv del usuario.
- En `.claude/settings.json` se usaron **tres listas de permisos**:
  - `deny` para operaciones inequívocamente destructivas (`rm -rf /`,
    `DROP TABLE`, `git push --force`).
  - `ask` para todo lo que pudiera afectar `bookshelf.db` (regla 4) y para
    cualquier `pip install` (regla 1) — fuerza el prompt de confirmación.
  - `allow` para las operaciones cotidianas (uvicorn, pytest, queries SQL
    de solo lectura, edición de archivos de proyecto).
- La skill se diseñó en `.claude/skills/bookshelf-tools/` con un `SKILL.md`
  que define la frontmatter y un `tools.py` que implementa tres subcomandos:
  - `seed` — postea 5 libros canónicos y 2-3 reseñas a través de la API.
  - `validate` — recorre cada endpoint del contrato y verifica status y
    forma del JSON.
  - `reset` — borra todos los libros vía API (con confirmación).
  El script no toca `bookshelf.db` directamente: todo va por HTTP. Esto
  respeta la regla 4 *por construcción*.

**Cosas que el agente eligió no hacer y avisó**: no corrió `pip install` por su
cuenta. Dejó el `requirements.txt` listo y esperó autorización.

### Fase 2 — Capa de datos y modelos

**Pedido**: `database.py`, `models.py` con cascada, `schemas.py` con tres
variantes por entidad. **Stop obligatorio** para revisar los schemas antes de
seguir.

**Decisiones**:

- `database.py`: engine SQLite con `check_same_thread=False` (necesario para
  FastAPI multi-thread), `SessionLocal` con `autoflush=False`, dependencia
  `get_db()` y helper `create_all()` invocable desde `main.py`.
- `models.py`: estilo SQLAlchemy 2.x (`Mapped[...]`, `mapped_column`). Cascada
  **en doble capa**: `cascade="all, delete-orphan"` en la relación ORM **y**
  `ondelete="CASCADE"` en la FK con `passive_deletes=True`. Esto garantiza el
  borrado tanto desde el ORM como si alguien dispara SQL directo.
- `schemas.py`: 4 variantes por entidad (`Base`, `Create`, `Update`, `Read`)
  con Pydantic v2 (`ConfigDict(from_attributes=True)` en los `*Read`). `rating`
  con `Field(ge=1, le=5)` para que un POST con `rating=99` dé 422 antes de
  tocar el router. `ReviewCreate` **no** incluye `book_id`: se toma de la URL,
  evitando inconsistencias entre path y body.

**Lo que pasó después de mostrar los schemas**: el arquitecto los revisó, los
aprobó tal cual, y se pasó a la Fase 3 sin cambios.

### Fase 3 — Capa de negocio y controladores

**Pedido**: `crud.py`, los dos routers con inyección de dependencias, y
`main.py` integrando todo con el mount estático al final.

**Decisiones**:

- `crud.py` separa estrictamente lectura/escritura:
  - `get_*` y `list_*` devuelven el modelo o `None` / lista vacía.
  - `delete_*` devuelve `bool`.
  - Las funciones sobre `Review` devuelven `None` si el `Book` no existe,
    para que el router lo traduzca a 404.
  - `update_book` usa `model_dump(exclude_unset=True)`: el PUT pisa solo lo
    que el cliente envió.
- En `routers/books.py` el prefix es `/api/books`. En `routers/reviews.py` el
  prefix es `/api` (no `/api/reviews`), porque sus rutas viven bajo dos raíces
  distintas: `/books/{id}/reviews` (listado y creación) y `/reviews/{id}`
  (baja). El docstring del módulo lo explica.
- `main.py` usa el patrón `lifespan` (el `on_event("startup")` está deprecado
  en FastAPI moderno). El mount de `StaticFiles` va **al final**, después de
  los `include_router`, para no interceptar las rutas de la API.

**Verificación**: tras aprobar el código, se autorizó instalar deps, se levantó
uvicorn, se corrió el validador de la skill: **15/15 checks verdes**. Después
el `seed` cargó los 5 libros y 8 reseñas.

### Fase 4 — Frontend vanilla

**Pedido**: `index.html`, `styles.css`, `app.js`, sin frameworks, sin bundlers,
sin imports.

**Decisiones de UI**:

- **Master-detail single-page**: dos `<section>` (`#list-view` y
  `#detail-view`) que se intercambian con `.hidden`. Sin rutas, sin History
  API. Cumple "una sola página" y es trivial de razonar.
- **Paleta madera/papel**: variables CSS con tonos marrón cálido y crema,
  serif para títulos (Georgia), system sans para texto. Sensación de
  biblioteca.
- **Toast no-bloqueante** arriba a la derecha (3s, autocierre) para feedback
  de éxito y error — más liviano que un alert.
- **`escapeHtml` propia** en todos los renders: como se inyecta con
  `.innerHTML`, evita XSS si alguien postea un nombre con `<script>`.
- **`window.confirm`** para borrados destructivos: alcanza para el alcance del
  TP, sin sumar deps.

**Iteración inesperada durante la verificación**: al simular el flujo en el
preview del navegador, el primer intento de publicar una reseña hizo que la
página **se recargara y volviera a la lista**. La hipótesis natural es "no se
llamó `preventDefault`", pero leyendo el código eso no podía ser.

Diagnóstico que terminó cerrando el caso:

1. Se inspeccionó el formulario en vivo (`form.method === "get"`, `action`
   apuntando a `/`) — el navegador iba a hacer un GET al raíz al submitear.
2. Se disparó el evento `submit` manualmente con
   `dispatchEvent(new Event('submit'))` — el handler **sí** corrió y **sí**
   llamó a `preventDefault`. La reseña apareció en la base.
3. Se reprodujo con `dispatchEvent(new MouseEvent('click'))` sobre el botón
   submit — todo funcionó.
4. Conclusión: la herramienta `preview_click` parece llamar a `form.submit()`
   (el método imperativo, que **bypassa** los listeners de `submit`) en vez de
   simular un click real del mouse. Un usuario haciendo click con el mouse o
   apretando Enter dispara el handler con normalidad.

El código no tenía bug; el aparente bug venía del simulador. Quedó como
recordatorio: **probar con eventos reales** cuando el comportamiento del
simulador no coincide con la realidad.

Una vez confirmado eso, se verificaron en el navegador, uno por uno, los ocho
flujos: cargar la lista, abrir un detalle, crear una reseña, editar un libro,
eliminar una reseña, volver al listado, crear un libro y eliminar un libro.

---

## 5. Iteración: agregar búsqueda de libros

Después de las cuatro fases originales se pidió **agregar una sección para
buscar libros indexando la base**. Esta iteración es interesante porque
ejercita el "flujo típico de funcionalidad nueva" que `CLAUDE.md` deja escrito
explícitamente.

### Conversación previa

Antes de tocar código, el agente hizo tres preguntas focalizadas:

1. **¿Sobre qué campos matchea la búsqueda?** Se eligió título + autor.
2. **¿Live (debounce mientras se tipea) o por botón / Enter?** Se eligió por
   botón / Enter — más predecible, una request explícita por búsqueda.
3. **¿Dónde colocamos la barra?** Se eligió arriba de la grilla, en la misma
   vista, sin sección nueva.

### Orden de implementación (regla 5)

El agente respetó estrictamente el orden:

1. **`CLAUDE.md` primero**: se agregó una subsección "Búsqueda de libros" al
   contrato, explicando que `GET /api/books` ahora acepta `?q=<texto>` con
   substring case-insensitive sobre `title` y `author`.
2. **`crud.py`**: `list_books(db, q=None)` con `func.lower(...).like("%q%")`
   sobre los dos campos vía `or_(...)`. La normalización a lowercase en ambos
   lados evita depender del collation por defecto de SQLite con caracteres
   acentuados.
3. **`routers/books.py`**: parámetro `q: str | None = Query(default=None,
   max_length=255)`. El `max_length` cubre el caso de query strings absurdamente
   largos.
4. **Tests** (regla 7): se creó `tests/conftest.py` con fixture `db` apuntando
   a SQLite en memoria, y `tests/test_crud_books_search.py` con 8 tests
   cubriendo: sin filtro, `q=None`, `q=""`, match por título, match por autor,
   case-insensitive, substring parcial, sin resultados. **8/8 PASS**.
5. **Frontend**: `<form id="search-form">` con input + botón Buscar + botón
   Limpiar arriba de la grilla; CSS coherente con la paleta existente; estado
   nuevo `currentQuery`; `apiGetBooks(q)` ampliado; `handleSearchSubmit` y
   `handleClearSearch` enganchados en `bindEvents()`. Mensaje específico
   *"No se encontraron libros que coincidan con la búsqueda."* cuando no hay
   resultados, distinto del *"Todavía no hay libros"* que aparece cuando la
   base está vacía. Resumen contextual *"N resultado(s) para «…»."* arriba de
   la grilla cuando hay query activa.
6. **Skill validator**: 3 checks nuevos para la búsqueda. El validador pasó
   de 15/15 a **18/18 PASS**.

### Verificación

Se reinició uvicorn (el preview lo había levantado sin `--reload`) y se probó
en el navegador la búsqueda por *borges* (1 resultado), un substring parcial
(*rayue* → "Rayuela"), una búsqueda sin resultados (mensaje específico
visible), y el botón Limpiar (vuelve a los 5 libros).

---

## 6. Estructura final del proyecto

```
bookshelf/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Entry point FastAPI
│   │   ├── database.py          # Engine, SessionLocal, get_db
│   │   ├── models.py            # SQLAlchemy: Book, Review
│   │   ├── schemas.py           # Pydantic v2: Base/Create/Update/Read
│   │   ├── crud.py              # Acceso a datos puro
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── books.py         # /api/books/*
│   │       └── reviews.py       # /api/books/{id}/reviews + /api/reviews/{id}
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Fixture db (SQLite en memoria)
│   │   └── test_crud_books_search.py
│   ├── requirements.txt
│   └── bookshelf.db             # Generado al arrancar (no versionado)
├── frontend/
│   ├── index.html               # Master-detail single-page
│   ├── styles.css
│   └── app.js                   # IIFE, sin imports
├── .claude/
│   ├── settings.json            # Permisos: deny / ask / allow
│   ├── launch.json              # Configuración para el preview
│   └── skills/
│       └── bookshelf-tools/
│           ├── SKILL.md
│           └── tools.py         # seed / validate / reset
├── CLAUDE.md                    # El contrato
└── README.md                    # Este archivo
```

---

## 7. Cómo levantarlo

```bash
cd backend
python -m venv .venv
source .venv/bin/activate         # Linux/Mac
# .venv\Scripts\activate          # Windows
pip install -r requirements.txt

uvicorn app.main:app --reload     # http://localhost:8000
```

- Frontend: `http://localhost:8000/`
- Swagger UI: `http://localhost:8000/docs`
- Tests: `pytest` desde `backend/`
- Poblar la base: `python ../.claude/skills/bookshelf-tools/tools.py seed`
- Validar el contrato: `python ../.claude/skills/bookshelf-tools/tools.py validate`

---

## 8. Resultados finales

| Validación                                          | Resultado    |
|-----------------------------------------------------|--------------|
| `pytest` (suite completa, DB en memoria)            | **8/8 PASS** |
| Validador del skill (`/bookshelf-tools validate`)   | **18/18 PASS** |
| Verificación manual en navegador (8 flujos UI)      | OK           |
| Verificación de la búsqueda (4 casos UI)            | OK           |

---

## 9. Aprendizajes del proceso

- **Escribir bien `CLAUDE.md` antes de empezar paga**. Cuanto más explícito el
  contrato, menos preguntas tontas durante el desarrollo y menos margen para
  que el agente improvise.
- **Las fases con stop intermedio son baratas**: cada pausa para revisar
  schemas o endpoints evita reescribir capas enteras más adelante.
- **Las reglas que dicen *"primero esto, después aquello"*** (regla 5: contrato
  antes que schemas antes que frontend) son lo que mantiene la coherencia
  entre capas en un proyecto que crece.
- **Las herramientas de simulación pueden mentir**. Confiar pero verificar:
  cuando el comportamiento simulado no coincide con la teoría, probar con
  eventos reales antes de "arreglar" código que no estaba roto.
