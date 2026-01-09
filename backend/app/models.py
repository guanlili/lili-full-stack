import datetime
import uuid

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# Scholar Models
class ScholarAuthor(SQLModel):
    name: str
    affiliation: str | None = None
    interests: list[str] | None = None
    citedby: int | None = None
    scholar_id: str
    url_picture: str | None = None


class ScholarPublication(SQLModel):
    title: str
    link: str | None = None
    snippet: str | None = None
    authors: str | None = None
    venue: str | None = None
    year: str | None = None
    cited_by: int | None = None
    versions: int | None = None
    detail: "PaperDetail | None" = None


class PaperDetail(SQLModel):
    title: str
    authors: list[str]
    publication_date: str | None = None
    venue: str | None = None
    doi: str | None = None
    source_site: str | None = None
    url: str
    abstract: str | None = None


class ScholarSearchResults(SQLModel):
    authors: list[ScholarAuthor]
    publications: list[ScholarPublication]
    count: int


class CacheEntry(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    key: str = Field(index=True, unique=True, max_length=512)
    result_json: str = Field(nullable=False)  # JSON serialized ScholarSearchResults
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class SearchHistory(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    key: str = Field(index=True, max_length=512)
    url: str | None = Field(default=None, max_length=1024)
    result_summary: str | None = Field(default=None, max_length=1024)
    source: str = Field(default="remote", max_length=16)  # "remote" or "cache"
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class ScholarExportData(SQLModel):
    publications: list[ScholarPublication]
    filename: str | None = "scholar_results.xlsx"

