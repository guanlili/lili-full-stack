from sqlmodel import SQLModel


class PageAccessPublic(SQLModel):
    path: str
    codename: str
    title: str
    admin_only: bool
    allowed: bool


class AccessPublic(SQLModel):
    pages: list[PageAccessPublic]
    permissions: list[str]
    is_admin: bool
