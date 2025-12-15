from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr


class AuthorIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class AuthorOut(AuthorIn):
    id: int


class LibraryIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address: str = Field(min_length=1, max_length=300)


class LibraryOut(LibraryIn):
    id: int


class BookIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    author_id: int
    library_id: int
    year: int | None = None


class BookOut(BookIn):
    id: int


class ContactIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class ContactOut(ContactIn):
    id: int
