import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlmodel import col, select

from app.api.deps import CurrentUser, SessionDep
from app.core.audit import record_audit
from app.core.config import settings
from app.models import FileAsset, FileAssetPublic

router = APIRouter(prefix="/files", tags=["files"])


def _file_path(asset: FileAsset) -> Path:
    return Path(settings.UPLOAD_DIR) / asset.stored_name


@router.post("/", response_model=FileAssetPublic, status_code=status.HTTP_201_CREATED)
async def upload_file(
    *, session: SessionDep, current_user: CurrentUser, file: UploadFile = File(...)
) -> FileAsset:
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    contents = await file.read(max_size + 1)
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size cannot exceed {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    original_name = Path(file.filename or "upload.bin").name[:255]
    suffix = Path(original_name).suffix.lower()
    asset = FileAsset(
        original_name=original_name,
        stored_name=f"{uuid.uuid4().hex}{suffix}",
        content_type=file.content_type,
        size=len(contents),
        owner_user_id=current_user.id,
    )
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    _file_path(asset).write_bytes(contents)
    session.add(asset)
    session.commit()
    session.refresh(asset)
    record_audit(
        session=session,
        actor=current_user,
        action="file.uploaded",
        resource_type="file",
        resource_id=asset.id,
        details={"name": asset.original_name, "size": asset.size},
    )
    return asset


@router.get("/", response_model=list[FileAssetPublic])
def read_files(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> list[FileAsset]:
    statement = select(FileAsset)
    if not current_user.is_superuser:
        statement = statement.where(col(FileAsset.owner_user_id) == current_user.id)
    return list(
        session.exec(
            statement.order_by(col(FileAsset.created_at).desc())
            .offset(skip)
            .limit(limit)
        ).all()
    )


@router.get("/{asset_id}")
def download_file(asset_id: uuid.UUID, session: SessionDep, current_user: CurrentUser):
    asset = session.get(FileAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and asset.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    path = _file_path(asset)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File content not found")
    return FileResponse(
        path,
        media_type=asset.content_type or "application/octet-stream",
        filename=asset.original_name,
    )


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    asset_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> None:
    asset = session.get(FileAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=404, detail="File not found")
    if not current_user.is_superuser and asset.owner_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Permission denied")
    _file_path(asset).unlink(missing_ok=True)
    session.delete(asset)
    session.commit()
    record_audit(
        session=session,
        actor=current_user,
        action="file.deleted",
        resource_type="file",
        resource_id=asset_id,
    )
