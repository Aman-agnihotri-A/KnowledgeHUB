from collections.abc import Callable
from uuid import UUID

from fastapi import Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.models.enums import UserRole
from app.models.user import User


def require_role(
    *allowed_roles: UserRole,
) -> Callable:
    def role_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return current_user

    return role_dependency


def require_tenant_access(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Allow SUPER_ADMIN to access any tenant while restricting
    TENANT_ADMIN and SUB_USER to their own tenant.
    """

    if current_user.role == UserRole.SUPER_ADMIN:
        return current_user

    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this tenant.",
        )

    return current_user

def require_tenant_admin_access(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Allow SUPER_ADMIN to manage users in any tenant.

    Allow TENANT_ADMIN to manage users only in their own tenant.

    SUB_USER is never allowed to manage tenant users.
    """

    if current_user.role == UserRole.SUPER_ADMIN:
        return current_user

    if (
        current_user.role == UserRole.TENANT_ADMIN
        and current_user.tenant_id == tenant_id
    ):
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have permission to manage tenant users.",
    )