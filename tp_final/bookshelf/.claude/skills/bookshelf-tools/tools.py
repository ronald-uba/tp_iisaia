"""
Herramientas de desarrollo para BookShelf.

Modos:
    python tools.py seed       # Pobla la API con datos de prueba
    python tools.py validate   # Valida el contrato API contra CLAUDE.md
    python tools.py reset      # Borra todos los libros vía API (requiere confirm)

Sin dependencias externas: usa urllib + json de la stdlib.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from typing import Any

BASE_URL = "http://localhost:8000/api"


# ---------------------------------------------------------------------------
# Cliente HTTP minimalista
# ---------------------------------------------------------------------------

def _request(method: str, path: str, body: dict | None = None) -> tuple[int, Any]:
    """Devuelve (status_code, payload_decodificado o None)."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            payload = json.loads(raw) if raw else None
            return resp.status, payload
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = {"detail": raw.decode("utf-8", errors="replace")}
        return exc.code, payload


def _server_reachable() -> bool:
    try:
        with urllib.request.urlopen("http://localhost:8000/docs", timeout=2) as resp:
            return resp.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False


# ---------------------------------------------------------------------------
# seed
# ---------------------------------------------------------------------------

SAMPLE_BOOKS = [
    {
        "title": "Cien años de soledad",
        "author": "Gabriel García Márquez",
        "published_year": 1967,
        "reviews": [
            {"reviewer_name": "Ana", "rating": 5, "comment": "Una obra maestra."},
            {"reviewer_name": "Luis", "rating": 4, "comment": "Compleja pero genial."},
        ],
    },
    {
        "title": "Ficciones",
        "author": "Jorge Luis Borges",
        "published_year": 1944,
        "reviews": [
            {"reviewer_name": "Marta", "rating": 5, "comment": "Cada cuento es un universo."},
        ],
    },
    {
        "title": "Rayuela",
        "author": "Julio Cortázar",
        "published_year": 1963,
        "reviews": [
            {"reviewer_name": "Pablo", "rating": 5, "comment": "Cambia la forma de leer."},
            {"reviewer_name": "Sofía", "rating": 3, "comment": "Difícil de seguir."},
        ],
    },
    {
        "title": "Pedro Páramo",
        "author": "Juan Rulfo",
        "published_year": 1955,
        "reviews": [
            {"reviewer_name": "Diego", "rating": 5, "comment": "Breve e intenso."},
        ],
    },
    {
        "title": "La invención de Morel",
        "author": "Adolfo Bioy Casares",
        "published_year": 1940,
        "reviews": [
            {"reviewer_name": "Lucía", "rating": 4, "comment": "Ciencia ficción adelantada."},
            {"reviewer_name": "Tomás", "rating": 5, "comment": "Perfecta en su forma."},
        ],
    },
]


def cmd_seed() -> int:
    print(">> Poblando base de datos con libros de ejemplo...")
    creados = 0
    resenas = 0
    for libro in SAMPLE_BOOKS:
        payload = {k: v for k, v in libro.items() if k != "reviews"}
        status, body = _request("POST", "/books", payload)
        if status != 201:
            print(f"   [FALLA] POST /books -> {status}: {body}")
            continue
        book_id = body["id"]
        creados += 1
        print(f"   [OK] Libro #{book_id}: {payload['title']}")
        for review in libro["reviews"]:
            s, b = _request("POST", f"/books/{book_id}/reviews", review)
            if s == 201:
                resenas += 1
                print(f"      [OK] Reseña de {review['reviewer_name']} ({review['rating']}★)")
            else:
                print(f"      [FALLA] POST review -> {s}: {b}")

    print(f"\n>> Listo: {creados} libros y {resenas} reseñas creadas.")
    return 0 if creados == len(SAMPLE_BOOKS) else 1


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------

def cmd_validate() -> int:
    """
    Recorre el contrato declarado en CLAUDE.md y reporta diferencias.
    Cada check imprime PASS o FAIL con detalle.
    """
    fallos: list[str] = []

    def check(nombre: str, condicion: bool, detalle: str = "") -> None:
        if condicion:
            print(f"   [PASS] {nombre}")
        else:
            print(f"   [FAIL] {nombre} -- {detalle}")
            fallos.append(nombre)

    print(">> Validando contrato API contra CLAUDE.md\n")

    # GET /api/books
    status, body = _request("GET", "/books")
    check("GET /api/books devuelve 200", status == 200, f"status={status}")
    check("GET /api/books devuelve lista", isinstance(body, list), f"body={type(body).__name__}")

    # POST /api/books -> 201
    nuevo = {"title": "Libro de prueba", "author": "Tester", "published_year": 2020}
    status, body = _request("POST", "/books", nuevo)
    check("POST /api/books devuelve 201", status == 201, f"status={status}")
    check(
        "POST /api/books devuelve recurso con id",
        isinstance(body, dict) and "id" in body,
        f"body={body}",
    )
    book_id = body["id"] if isinstance(body, dict) and "id" in body else None

    # POST /api/books con payload inválido -> 422
    status, body = _request("POST", "/books", {"author": "sin titulo"})
    check("POST /api/books con payload inválido devuelve 422", status == 422, f"status={status}")

    if book_id is not None:
        # GET /api/books/{id}
        status, body = _request("GET", f"/books/{book_id}")
        check(f"GET /api/books/{book_id} devuelve 200", status == 200, f"status={status}")

        # PUT /api/books/{id}
        status, body = _request("PUT", f"/books/{book_id}", {"title": "Libro editado"})
        check(f"PUT /api/books/{book_id} devuelve 200", status == 200, f"status={status}")

        # POST review
        review = {"reviewer_name": "Validador", "rating": 4, "comment": "ok"}
        status, body = _request("POST", f"/books/{book_id}/reviews", review)
        check("POST /api/books/{id}/reviews devuelve 201", status == 201, f"status={status}")
        review_id = body["id"] if isinstance(body, dict) and "id" in body else None

        # Rating fuera de rango -> 422
        mal = {"reviewer_name": "X", "rating": 99, "comment": "fuera de rango"}
        status, _ = _request("POST", f"/books/{book_id}/reviews", mal)
        check("POST review con rating>5 devuelve 422", status == 422, f"status={status}")

        # GET reviews del libro
        status, body = _request("GET", f"/books/{book_id}/reviews")
        check("GET /api/books/{id}/reviews devuelve 200", status == 200, f"status={status}")
        check("GET reviews devuelve lista", isinstance(body, list), f"body={type(body).__name__}")

        # DELETE review
        if review_id is not None:
            status, _ = _request("DELETE", f"/reviews/{review_id}")
            check("DELETE /api/reviews/{id} devuelve 204", status == 204, f"status={status}")

        # DELETE book -> 204 + cascada
        status, _ = _request("DELETE", f"/books/{book_id}")
        check(f"DELETE /api/books/{book_id} devuelve 204", status == 204, f"status={status}")

        # GET tras DELETE -> 404
        status, _ = _request("GET", f"/books/{book_id}")
        check("GET de libro borrado devuelve 404", status == 404, f"status={status}")

    # 404 sobre id inexistente
    status, _ = _request("GET", "/books/999999")
    check("GET /api/books/999999 devuelve 404", status == 404, f"status={status}")

    # Búsqueda con ?q=
    # Insertamos un libro reconocible y probamos que la búsqueda lo encuentre.
    marker = {"title": "ZZ-Marker-Search", "author": "Tester Marker", "published_year": 2024}
    status, body = _request("POST", "/books", marker)
    marker_id = body["id"] if status == 201 and isinstance(body, dict) else None

    status, body = _request("GET", "/books?q=zz-marker")
    check(
        "GET /api/books?q=zz-marker encuentra el libro insertado",
        isinstance(body, list) and any(b.get("id") == marker_id for b in body),
        f"status={status} body={body}",
    )

    status, body = _request("GET", "/books?q=TESTER")
    check(
        "GET /api/books?q=TESTER es case-insensitive",
        isinstance(body, list) and any(b.get("id") == marker_id for b in body),
        f"status={status}",
    )

    status, body = _request("GET", "/books?q=zzz-no-existe-xx")
    check(
        "GET /api/books?q=zzz-no-existe-xx devuelve lista vacía",
        isinstance(body, list) and len(body) == 0,
        f"status={status} body={body}",
    )

    if marker_id is not None:
        _request("DELETE", f"/books/{marker_id}")

    print()
    if fallos:
        print(f">> {len(fallos)} chequeo(s) fallaron:")
        for f in fallos:
            print(f"   - {f}")
        return 1
    print(">> Todos los chequeos pasaron. La API respeta el contrato.")
    return 0


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------

def cmd_reset() -> int:
    print(">> Borrando todos los libros vía API (cascada sobre reseñas)...")
    status, body = _request("GET", "/books")
    if status != 200 or not isinstance(body, list):
        print(f"   [FALLA] No se pudo listar: status={status}")
        return 1
    for libro in body:
        bid = libro.get("id")
        s, _ = _request("DELETE", f"/books/{bid}")
        marca = "OK" if s == 204 else f"FALLA ({s})"
        print(f"   [{marca}] DELETE /books/{bid}")
    print(">> Reset completo.")
    return 0


# ---------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------

COMMANDS = {
    "seed": cmd_seed,
    "validate": cmd_validate,
    "reset": cmd_reset,
}


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in COMMANDS:
        print(__doc__)
        return 2
    if not _server_reachable():
        print("ERROR: el servidor no responde en http://localhost:8000")
        print("Levantalo con:  cd backend && uvicorn app.main:app --reload")
        return 3
    return COMMANDS[argv[1]]()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
