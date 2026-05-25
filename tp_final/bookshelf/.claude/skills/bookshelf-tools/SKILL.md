---
name: bookshelf-tools
description: Herramientas de desarrollo para el proyecto BookShelf. Permite poblar la base de datos con datos de prueba (`seed`) o validar el contrato de la API contra los endpoints definidos en CLAUDE.md (`validate`). Invocable como `/bookshelf-tools seed` o `/bookshelf-tools validate`. Requiere que el servidor uvicorn esté corriendo en http://localhost:8000.
---

# bookshelf-tools

Skill propia del proyecto BookShelf. Asiste al desarrollador con dos tareas comunes durante la iteración:

1. **`seed`**: pobla la base de datos con un conjunto fijo de libros y reseñas de ejemplo. Útil tras borrar `bookshelf.db` o al levantar el entorno por primera vez.
2. **`validate`**: ejecuta una batería de chequeos contra los endpoints definidos en `CLAUDE.md` (códigos de estado, formato de respuesta, comportamiento de la cascada de borrado) y reporta diferencias respecto al contrato.

## Cómo usar esta skill

Cuando el usuario invoque `/bookshelf-tools <subcomando>`:

1. Verificá que el servidor esté corriendo:
   ```bash
   curl -sf http://localhost:8000/docs > /dev/null
   ```
   Si no responde, indicale al usuario que levante uvicorn con:
   ```bash
   cd backend && uvicorn app.main:app --reload
   ```
   No avances hasta confirmar disponibilidad.

2. Ejecutá el script correspondiente:
   - `seed` → `python .claude/skills/bookshelf-tools/tools.py seed`
   - `validate` → `python .claude/skills/bookshelf-tools/tools.py validate`

3. Mostrá la salida íntegra al usuario. Si `validate` encuentra fallos, listalos como puntos a corregir en la próxima fase.

## Subcomandos disponibles

| Subcomando  | Acción                                                                 |
|-------------|------------------------------------------------------------------------|
| `seed`      | Crea 5 libros y 2-3 reseñas por libro vía POST a `/api/...`.           |
| `validate`  | Recorre cada endpoint del contrato y verifica status y forma del JSON. |
| `reset`     | (requiere confirmación) borra todos los libros vía DELETE.             |

## Restricciones

- La skill **nunca** toca `bookshelf.db` directamente con sqlite3 ni con `rm`. Toda interacción es vía HTTP a la API, respetando la regla 4 de CLAUDE.md (no borrar la base sin confirmación).
- Si el usuario pide `reset`, pediles confirmación explícita antes de ejecutarlo.
- No instala dependencias. El script usa solo `urllib` y `json` de la stdlib.
