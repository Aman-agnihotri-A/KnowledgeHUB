import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.authorization import (
    require_role,
    require_tenant_access,
    require_tenant_admin_access,
)
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.tenant import TenantCreate, TenantRead
from app.schemas.user import (
    UserCreate,
    UserRead,
    UserStatusUpdate,
)
from app.services.tenant import TenantService
from app.services.user import UserService


router = APIRouter(
    prefix="/tenants",
    tags=["tenants"],
)

tenant_service = TenantService()
user_service = UserService()


@router.post(
    "",
    response_model=TenantRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant(
    payload: TenantCreate,
    current_user: User = Depends(
        require_role(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
) -> TenantRead:
    try:
        return tenant_service.create_tenant(
            db,
            name=payload.name,
            slug=payload.slug,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[TenantRead],
)
def list_tenants(
    current_user: User = Depends(
        require_role(UserRole.SUPER_ADMIN)
    ),
    db: Session = Depends(get_db),
) -> list[TenantRead]:
    return tenant_service.list_active_tenants(db)


@router.get(
    "/{tenant_id}",
    response_model=TenantRead,
)
def get_tenant(
    tenant_id: uuid.UUID,
    current_user: User = Depends(require_tenant_access),
    db: Session = Depends(get_db),
) -> TenantRead:
    tenant = tenant_service.get_tenant(
        db,
        tenant_id,
    )

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    return tenant


@router.post(
    "/{tenant_id}/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tenant_user(
    tenant_id: uuid.UUID,
    payload: UserCreate,
    current_user: User = Depends(
        require_tenant_admin_access
    ),
    db: Session = Depends(get_db),
) -> UserRead:
    if (
        current_user.role == UserRole.TENANT_ADMIN
        and payload.role != UserRole.SUB_USER
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Tenant Admin can only create Sub Users."
            ),
        )

    if payload.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin users cannot be created here.",
        )

    try:
        return user_service.create_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            role=payload.role,
            tenant_id=tenant_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "/{tenant_id}/users",
    response_model=list[UserRead],
)
def list_tenant_users(
    tenant_id: uuid.UUID,
    current_user: User = Depends(
        require_tenant_admin_access
    ),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    return user_service.list_active_tenant_users(
        db,
        tenant_id,
    )
@router.patch(
    "/{tenant_id}/users/{user_id}/status",
    response_model=UserRead,
)
def update_tenant_user_status(
    tenant_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    current_user: User = Depends(
        require_tenant_admin_access
    ),
    db: Session = Depends(get_db),
) -> UserRead:
    
    try:
        user = user_service.get_user(
            db,
            user_id,
        )

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if (
            current_user.role == UserRole.TENANT_ADMIN
            and user.role != UserRole.SUB_USER
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant Admin can only manage Sub Users.",
            )

        return user_service.update_user_status(
            db,
            user_id=user_id,
            tenant_id=tenant_id,
            is_active=payload.is_active,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc