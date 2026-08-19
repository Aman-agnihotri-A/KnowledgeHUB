from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.user import UserService


router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
)

user_service = UserService()


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = user_service.authenticate_user(
        db,
        email=payload.email,
        password=payload.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(
        user_id=str(user.id),
        role=user.role.value,
        tenant_id=(
            str(user.tenant_id)
            if user.tenant_id is not None
            else None
        ),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )