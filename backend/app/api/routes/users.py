import csv
import io
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import col, func, select

from app import crud
from app.api.deps import (
    CurrentUser,
    SessionDep,
    get_current_active_superuser,
)
from app.core.audit import record_audit
from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.core.sessions import revoke_user_refresh_tokens
from app.models import (
    Message,
    UpdatePassword,
    User,
    UserCreate,
    UserImportResult,
    UserPublic,
    UserRegister,
    UsersPublic,
    UserUpdate,
    UserUpdateMe,
)
from app.utils import generate_new_account_email, send_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UsersPublic,
)
def read_users(session: SessionDep, skip: int = 0, limit: int = 100) -> Any:
    """
    Retrieve users.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = (
        select(User).order_by(col(User.created_at).desc()).offset(skip).limit(limit)
    )
    users = session.exec(statement).all()

    users_public = [UserPublic.model_validate(user) for user in users]
    return UsersPublic(data=users_public, count=count)


@router.post(
    "/", dependencies=[Depends(get_current_active_superuser)], response_model=UserPublic
)
def create_user(
    *, session: SessionDep, user_in: UserCreate, current_user: CurrentUser
) -> Any:
    """
    Create new user.
    """
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    user = crud.create_user(session=session, user_create=user_in)
    record_audit(
        session=session,
        actor=current_user,
        action="user.created",
        resource_type="user",
        resource_id=user.id,
        details={"email": str(user.email)},
    )
    if settings.emails_enabled and user_in.email:
        email_data = generate_new_account_email(
            email_to=user_in.email, username=user_in.email
        )
        send_email(
            email_to=user_in.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return user


@router.patch("/me", response_model=UserPublic)
def update_user_me(
    *, session: SessionDep, user_in: UserUpdateMe, current_user: CurrentUser
) -> Any:
    """
    Update own user.
    """

    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )
    user_data = user_in.model_dump(exclude_unset=True)
    current_user.sqlmodel_update(user_data)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.patch("/me/password", response_model=Message)
def update_password_me(
    *, session: SessionDep, body: UpdatePassword, current_user: CurrentUser
) -> Any:
    """
    Update own password.
    """
    verified, _ = verify_password(body.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=400, detail="Incorrect password")
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=400, detail="New password cannot be the same as the current one"
        )
    hashed_password = get_password_hash(body.new_password)
    current_user.hashed_password = hashed_password
    current_user.token_version += 1
    revoke_user_refresh_tokens(session=session, user_id=current_user.id)
    session.add(current_user)
    session.commit()
    record_audit(
        session=session,
        actor=current_user,
        action="user.password_changed",
        resource_type="user",
        resource_id=current_user.id,
    )
    return Message(message="Password updated successfully")


@router.get("/me", response_model=UserPublic)
def read_user_me(current_user: CurrentUser) -> Any:
    """
    Get current user.
    """
    return current_user


@router.delete("/me", response_model=Message)
def delete_user_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """
    Delete own user.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(current_user)
    session.commit()
    return Message(message="User deleted successfully")


@router.post("/signup", response_model=UserPublic)
def register_user(session: SessionDep, user_in: UserRegister) -> Any:
    """
    Create new user without the need to be logged in.
    """
    if not settings.USERS_OPEN_REGISTRATION:
        raise HTTPException(
            status_code=403,
            detail="Open user registration is forbidden on this server",
        )
    user = crud.get_user_by_email(session=session, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system",
        )
    user_create = UserCreate.model_validate(user_in)
    user = crud.create_user(session=session, user_create=user_create)
    return user


@router.get(
    "/export.csv",
    dependencies=[Depends(get_current_active_superuser)],
)
def export_users(session: SessionDep) -> StreamingResponse:
    """Export non-sensitive user fields as UTF-8 CSV."""
    users = session.exec(select(User).order_by(col(User.created_at))).all()

    def rows():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            ["email", "full_name", "is_active", "is_superuser", "created_at"]
        )
        yield output.getvalue()
        for user in users:
            output = io.StringIO()
            csv.writer(output).writerow(
                [
                    user.email,
                    user.full_name or "",
                    user.is_active,
                    user.is_superuser,
                    user.created_at.isoformat() if user.created_at else "",
                ]
            )
            yield output.getvalue()

    return StreamingResponse(
        rows(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@router.post(
    "/import.csv",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserImportResult,
)
async def import_users(
    *, session: SessionDep, current_user: CurrentUser, file: UploadFile = File(...)
) -> UserImportResult:
    """Import users from CSV columns: email,password,full_name,is_active."""
    contents = await file.read(2 * 1024 * 1024 + 1)
    if len(contents) > 2 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="CSV file cannot exceed 2 MB")
    try:
        reader = csv.DictReader(io.StringIO(contents.decode("utf-8-sig")))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8") from exc
    required = {"email", "password"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise HTTPException(
            status_code=400,
            detail="CSV must contain email and password columns",
        )

    errors: list[str] = []
    created_count = 0
    for row_number, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip()
        password = row.get("password") or ""
        if not email or len(password) < 8:
            errors.append(
                f"row {row_number}: email is required and password must be 8+ characters"
            )
            continue
        if crud.get_user_by_email(session=session, email=email):
            errors.append(f"row {row_number}: email already exists")
            continue
        try:
            user_in = UserCreate(
                email=email,
                password=password,
                full_name=(row.get("full_name") or "").strip() or None,
                is_active=(row.get("is_active") or "true").lower() != "false",
                is_superuser=False,
            )
            user = crud.create_user(session=session, user_create=user_in)
            record_audit(
                session=session,
                actor=current_user,
                action="user.imported",
                resource_type="user",
                resource_id=user.id,
                details={"email": str(user.email), "row": row_number},
            )
            created_count += 1
        except Exception as exc:
            session.rollback()
            errors.append(f"row {row_number}: invalid user data ({type(exc).__name__})")
    return UserImportResult(created_count=created_count, errors=errors)


@router.get("/{user_id}", response_model=UserPublic)
def read_user_by_id(
    user_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> Any:
    """
    Get a specific user by id.
    """
    user = session.get(User, user_id)
    if user == current_user:
        return user
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="The user doesn't have enough privileges",
        )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=UserPublic,
)
def update_user(
    *,
    session: SessionDep,
    user_id: uuid.UUID,
    user_in: UserUpdate,
    current_user: CurrentUser,
) -> Any:
    """
    Update a user.
    """

    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(
            status_code=404,
            detail="The user with this id does not exist in the system",
        )
    if user_in.email:
        existing_user = crud.get_user_by_email(session=session, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=409, detail="User with this email already exists"
            )

    db_user = crud.update_user(session=session, db_user=db_user, user_in=user_in)
    if user_in.password is not None:
        revoke_user_refresh_tokens(session=session, user_id=db_user.id)
    record_audit(
        session=session,
        actor=current_user,
        action="user.updated",
        resource_type="user",
        resource_id=db_user.id,
        details={"fields": list(user_in.model_dump(exclude_unset=True))},
    )
    return db_user


@router.delete("/{user_id}", dependencies=[Depends(get_current_active_superuser)])
def delete_user(
    session: SessionDep, current_user: CurrentUser, user_id: uuid.UUID
) -> Message:
    """
    Delete a user.
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user == current_user:
        raise HTTPException(
            status_code=403, detail="Super users are not allowed to delete themselves"
        )
    session.delete(user)
    session.commit()
    record_audit(
        session=session,
        actor=current_user,
        action="user.deleted",
        resource_type="user",
        resource_id=user_id,
    )
    return Message(message="User deleted successfully")
