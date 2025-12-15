from __future__ import annotations
from fastapi import FastAPI, HTTPException, Query
from typing import Any
from .db import connect, init_db
from .models import (
    AuthorIn, AuthorOut,
    LibraryIn, LibraryOut,
    BookIn, BookOut,
    ContactIn, ContactOut,
)

app = FastAPI(
    title="Practikum REST API (Python)",
    version="1.0.0",
    docs_url="/docs",     # Swagger
    redoc_url="/redoc",   # ReDoc
    openapi_url="/openapi.json"
)



@app.on_event("startup")
def _startup() -> None:
    init_db()


def _row_to_dict(row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


# ---------- AUTHORS ----------
@app.post("/authors", response_model=AuthorOut, status_code=201)
def create_author(payload: AuthorIn):
    with connect() as conn:
        cur = conn.execute("INSERT INTO authors(name) VALUES(?)", (payload.name,))
        author_id = cur.lastrowid
        row = conn.execute("SELECT id, name FROM authors WHERE id=?", (author_id,)).fetchone()
    return _row_to_dict(row)


@app.get("/authors", response_model=list[AuthorOut])
def list_authors(q: str | None = None):
    with connect() as conn:
        if q:
            rows = conn.execute("SELECT id, name FROM authors WHERE name LIKE ? ORDER BY id", (f"%{q}%",)).fetchall()
        else:
            rows = conn.execute("SELECT id, name FROM authors ORDER BY id").fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/authors/{author_id}", response_model=AuthorOut)
def get_author(author_id: int):
    with connect() as conn:
        row = conn.execute("SELECT id, name FROM authors WHERE id=?", (author_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Author not found")
    return _row_to_dict(row)


@app.delete("/authors/{author_id}", status_code=204)
def delete_author(author_id: int):
    with connect() as conn:
        cur = conn.execute("DELETE FROM authors WHERE id=?", (author_id,))
    if cur.rowcount == 0:
        raise HTTPException(404, "Author not found")


@app.post("/libraries", response_model=LibraryOut, status_code=201)
def create_library(payload: LibraryIn):
    with connect() as conn:
        cur = conn.execute("INSERT INTO libraries(name, address) VALUES(?,?)", (payload.name, payload.address))
        lib_id = cur.lastrowid
        row = conn.execute("SELECT id, name, address FROM libraries WHERE id=?", (lib_id,)).fetchone()
    return _row_to_dict(row)


@app.get("/libraries", response_model=list[LibraryOut])
def list_libraries():
    with connect() as conn:
        rows = conn.execute("SELECT id, name, address FROM libraries ORDER BY id").fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/libraries/{library_id}", response_model=LibraryOut)
def get_library(library_id: int):
    with connect() as conn:
        row = conn.execute("SELECT id, name, address FROM libraries WHERE id=?", (library_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Library not found")
    return _row_to_dict(row)


@app.post("/books", response_model=BookOut, status_code=201)
def create_book(payload: BookIn):
    with connect() as conn:
        a = conn.execute("SELECT 1 FROM authors WHERE id=?", (payload.author_id,)).fetchone()
        l = conn.execute("SELECT 1 FROM libraries WHERE id=?", (payload.library_id,)).fetchone()
        if not a:
            raise HTTPException(400, "author_id does not exist")
        if not l:
            raise HTTPException(400, "library_id does not exist")

        cur = conn.execute(
            "INSERT INTO books(title, author_id, library_id, year) VALUES(?,?,?,?)",
            (payload.title, payload.author_id, payload.library_id, payload.year),
        )
        book_id = cur.lastrowid
        row = conn.execute(
            "SELECT id, title, author_id, library_id, year FROM books WHERE id=?",
            (book_id,),
        ).fetchone()
    return _row_to_dict(row)


@app.get("/books", response_model=list[BookOut])
def list_books(
    author_id: int | None = None,
    library_id: int | None = None,
    _sort: str | None = Query(default=None, description="json-server style: _sort=title|year"),
):
    sql = "SELECT id, title, author_id, library_id, year FROM books"
    params: list[Any] = []
    where: list[str] = []
    if author_id is not None:
        where.append("author_id=?")
        params.append(author_id)
    if library_id is not None:
        where.append("library_id=?")
        params.append(library_id)
    if where:
        sql += " WHERE " + " AND ".join(where)
    if _sort in {"title", "year", "id"}:
        sql += f" ORDER BY {_sort}"
    else:
        sql += " ORDER BY id"

    with connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return [_row_to_dict(r) for r in rows]


@app.get("/books/{book_id}", response_model=BookOut)
def get_book(book_id: int):
    with connect() as conn:
        row = conn.execute(
            "SELECT id, title, author_id, library_id, year FROM books WHERE id=?",
            (book_id,),
        ).fetchone()
    if not row:
        raise HTTPException(404, "Book not found")
    return _row_to_dict(row)


@app.put("/books/{book_id}", response_model=BookOut)
def update_book(book_id: int, payload: BookIn):
    with connect() as conn:
        cur = conn.execute(
            "UPDATE books SET title=?, author_id=?, library_id=?, year=? WHERE id=?",
            (payload.title, payload.author_id, payload.library_id, payload.year, book_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Book not found")
        row = conn.execute(
            "SELECT id, title, author_id, library_id, year FROM books WHERE id=?",
            (book_id,),
        ).fetchone()
    return _row_to_dict(row)


@app.delete("/books/{book_id}", status_code=204)
def delete_book(book_id: int):
    with connect() as conn:
        cur = conn.execute("DELETE FROM books WHERE id=?", (book_id,))
    if cur.rowcount == 0:
        raise HTTPException(404, "Book not found")


# ---------- CONTACTS (из практики CRUD, телефонная книга) ----------
@app.post("/v1/contact", response_model=ContactOut, status_code=201)
def create_contact(payload: ContactIn):
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO contacts(first_name,last_name,email) VALUES(?,?,?)",
            (payload.first_name, payload.last_name, str(payload.email)),
        )
        cid = cur.lastrowid
        row = conn.execute(
            "SELECT id, first_name, last_name, email FROM contacts WHERE id=?",
            (cid,),
        ).fetchone()
    return _row_to_dict(row)


@app.get("/v1/contact", response_model=list[ContactOut])
def list_contacts(email: str | None = None):
    with connect() as conn:
        if email:
            rows = conn.execute(
                "SELECT id, first_name, last_name, email FROM contacts WHERE email=? ORDER BY id",
                (email,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT id, first_name, last_name, email FROM contacts ORDER BY id").fetchall()
    return [_row_to_dict(r) for r in rows]


@app.delete("/v1/contact", status_code=204)
def delete_all_contacts():
    with connect() as conn:
        conn.execute("DELETE FROM contacts")


@app.get("/v1/contact/{uid}", response_model=ContactOut)
def get_contact(uid: int):
    with connect() as conn:
        row = conn.execute("SELECT id, first_name, last_name, email FROM contacts WHERE id=?", (uid,)).fetchone()
    if not row:
        raise HTTPException(404, "Contact not found")
    return _row_to_dict(row)


@app.put("/v1/contact/{uid}", response_model=ContactOut)
def update_contact(uid: int, payload: ContactIn):
    with connect() as conn:
        cur = conn.execute(
            "UPDATE contacts SET first_name=?, last_name=?, email=? WHERE id=?",
            (payload.first_name, payload.last_name, str(payload.email), uid),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Contact not found")
        row = conn.execute("SELECT id, first_name, last_name, email FROM contacts WHERE id=?", (uid,)).fetchone()
    return _row_to_dict(row)


@app.delete("/v1/contact/{uid}", status_code=204)
def delete_contact(uid: int):
    with connect() as conn:
        cur = conn.execute("DELETE FROM contacts WHERE id=?", (uid,))
    if cur.rowcount == 0:
        raise HTTPException(404, "Contact not found")
