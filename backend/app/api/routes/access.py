from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.core.permissions import PAGES, effective_permissions
from app.models import AccessPublic, PageAccessPublic

router = APIRouter(prefix="/access", tags=["access"])


@router.get("/me", response_model=AccessPublic)
def read_access(session: SessionDep, current_user: CurrentUser) -> AccessPublic:
    permissions = effective_permissions(session, current_user)
    return AccessPublic(
        is_admin=current_user.is_superuser,
        permissions=sorted(permissions),
        pages=[
            PageAccessPublic(
                path=page.path,
                codename=page.codename,
                title=page.title,
                admin_only=page.admin_only,
                allowed=page.codename in permissions,
            )
            for page in PAGES
        ],
    )
