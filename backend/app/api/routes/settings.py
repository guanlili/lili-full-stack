import re

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import col, select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core.audit import record_audit
from app.models import SystemSetting, SystemSettingPublic, SystemSettingUpdate

router = APIRouter(prefix="/settings", tags=["settings"])
KEY_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,99}$")
SECRET_KEY_PATTERN = re.compile(r"(?:password|secret|token|private|api[-_]?key)", re.I)


@router.get(
    "/",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=list[SystemSettingPublic],
)
def read_settings(session: SessionDep) -> list[SystemSetting]:
    return list(
        session.exec(select(SystemSetting).order_by(col(SystemSetting.key))).all()
    )


@router.put(
    "/{key}",
    dependencies=[Depends(get_current_active_superuser)],
    response_model=SystemSettingPublic,
)
def update_setting(
    *,
    session: SessionDep,
    key: str,
    body: SystemSettingUpdate,
    current_user: CurrentUser,
) -> SystemSetting:
    if not KEY_PATTERN.fullmatch(key):
        raise HTTPException(status_code=422, detail="Invalid setting key")
    if SECRET_KEY_PATTERN.search(key):
        raise HTTPException(
            status_code=400,
            detail="Sensitive values must use environment secrets",
        )
    setting = session.get(SystemSetting, key)
    if setting is None:
        setting = SystemSetting(key=key, value=body.value, description=body.description)
    else:
        setting.value = body.value
        setting.description = body.description
    session.add(setting)
    session.commit()
    session.refresh(setting)
    record_audit(
        session=session,
        actor=current_user,
        action="setting.updated",
        resource_type="setting",
        resource_id=key,
    )
    return setting
